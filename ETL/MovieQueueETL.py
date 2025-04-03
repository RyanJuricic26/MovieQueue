import pandas as pd
import ast
from tqdm import tqdm
from collections import defaultdict
from Database.Neo4j_Connection import Connect
from ETL_config import BATCH_SIZE, TOP_K, MOVIE_DATA_PATH, RATINGS_DATA_PATH, PEOPLE_DATA_PATH, PRINCIPALS_DATA_PATH, REL_OUTPUT_DIR
import os

os.makedirs(REL_OUTPUT_DIR, exist_ok=True)

# ==============================
# FILTER MOVIES
# ==============================
def filter_top_movies(movie_csv, rating_csv):
    print("\n[STEP 1] Filtering Movies...")

    df = pd.read_csv(movie_csv, delimiter='\t')
    ratings = pd.read_csv(rating_csv, delimiter='\t')
    df = df[df['titleType'] == 'movie']

    merged_data = df.merge(ratings, how='left', on='tconst')

    merged_data = merged_data[merged_data['numVotes'].apply(lambda x: x.isnumeric())]
    merged_data['numVotes'] = merged_data['numVotes'].astype(int)

    merged_data['genres'] = merged_data['genres'].fillna("").apply(lambda x: x.split(",") if x else [])
    merged_data.loc[df['isAdult'] == 1, 'genres'] = merged_data.loc[df['isAdult'] == 1, 'genres'].apply(lambda g: g + ['Adult'])

    df_exploded = merged_data.explode('genres')

    top_movies = df_exploded.groupby('genres', group_keys=False).apply(lambda x: x.nlargest(TOP_K, 'numVotes'))
    top_movies = top_movies.drop_duplicates('tconst')

    print(f"[INFO] Filtered down to {len(top_movies)} top movies.")
    return top_movies

# ==============================
# FILTER PEOPLE
# ==============================
def filter_people(people_csv, principals_csv, valid_movie_ids):
    df_p = pd.read_csv(principals_csv, delimiter='\t')
    df_p = df_p[df_p['tconst'].isin(valid_movie_ids)]

    involved_people = set(df_p['nconst'].unique())

    df_people = pd.read_csv(people_csv, delimiter='\t')
    df_people = df_people[df_people['nconst'].isin(involved_people)]

    return df_people, df_p

# ==============================
# BUILD RELATIONSHIP CSVs
# ==============================
def build_relationship_csvs(df_p):
    print("[STEP 2] Generating Relationship Files...")

    relationship_map = defaultdict(list)

    for _, row in df_p.iterrows():
        tconst = row['tconst']
        nconst = row['nconst']
        category = row['category']
        job = row.get('job', '')
        characters = row.get('characters', '')

        if category == 'actor' or category == 'actress':
            relationship_map['ACTED_IN'].append({'tconst': tconst, 'nconst': nconst, 'characters': characters})
        elif category == 'self':
            relationship_map['APPEARED_AS_SELF_IN'].append({'tconst': tconst, 'nconst': nconst})
        elif category == 'director':
            relationship_map['DIRECTED'].append({'tconst': tconst, 'nconst': nconst})
        else:
            relationship_map[job.upper()].append({'tconst': tconst, 'nconst': nconst})

    for rel, rows in relationship_map.items():
        df_rel = pd.DataFrame(rows)
        df_rel.to_csv(f"{REL_OUTPUT_DIR}/{rel}.csv", index=False)
        print(f"[INFO] Saved {rel}.csv with {len(df_rel)} records.")

# ==============================
# UPLOAD MOVIES
# ==============================
def upload_movies(df):
    db = Connect()
    with db._driver.session() as session:
        for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Uploading Movies"):
            batch = df.iloc[i:i+BATCH_SIZE].to_dict(orient="records")
            session.run("""
            UNWIND $movies AS movie
            MERGE (m:Movie {id: movie.tconst})
            ON CREATE SET
                m.primaryTitle = movie.primaryTitle,
                m.startYear = toInteger(movie.startYear),
                m.runtimeMinutes = CASE WHEN movie.runtimeMinutes=\"\\N\" THEN NULL ELSE toInteger(movie.runtimeMinutes) END,
                m.averageRating = CASE WHEN movie.averageRating=\"\\N\" THEN NULL ELSE toFloat(movie.averageRating) END,
                m.numVotes = movie.numVotes

            FOREACH (genre IN movie.genres |
                MERGE (g:Genre {name: genre})
                MERGE (m)-[:HAS_GENRE]->(g)
            )
            """, {"movies": batch})

# ==============================
# UPLOAD PEOPLE
# ==============================
def upload_people(df):
    db = Connect()
    df["birthYear"] = df["birthYear"].fillna(0).astype(int)
    df["deathYear"] = df["deathYear"].fillna(0).astype(int)
    df["primaryProfession"] = df["primaryProfession"].apply(lambda x: x.split(",") if pd.notna(x) else [])

    with db._driver.session() as session:
        for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Uploading People"):
            batch = df.iloc[i:i+BATCH_SIZE].to_dict(orient="records")
            session.run("""
            UNWIND $people AS person
            MERGE (p:Person {id: person.nconst})
            ON CREATE SET
                p.name = person.primaryName,
                p.birthYear = CASE WHEN person.birthYear=0 THEN NULL ELSE person.birthYear END,
                p.deathYear = CASE WHEN person.deathYear=0 THEN NULL ELSE person.deathYear END

            FOREACH (prof IN person.primaryProfession |
                MERGE (pr:Profession {name: prof})
                MERGE (p)-[:HAS_PROFESSION]->(pr)
            )
            """, {"people": batch})

# ==============================
# UPLOAD RELATIONSHIPS
# ==============================
def upload_relationships():
    db = Connect()

    for file in os.listdir(REL_OUTPUT_DIR):
        if not file.endswith(".csv"): continue

        rel_type = file.replace(".csv", "")
        df = pd.read_csv(f"{REL_OUTPUT_DIR}/{file}")

        with db._driver.session() as session:
            for i in tqdm(range(0, len(df), BATCH_SIZE), desc=f"Uploading {rel_type}"):
                batch = df.iloc[i:i+BATCH_SIZE].to_dict(orient="records")
                if rel_type == "ACTED_IN":
                    for row in batch:
                        row["characters"] = ast.literal_eval(row["characters"]) if pd.notna(row["characters"]) and row["characters"].startswith("[") else []

                    session.run("""
                    UNWIND $rels AS rel
                    MATCH (p:Person {id: rel.nconst})
                    MATCH (m:Movie {id: rel.tconst})
                    MERGE (p)-[r:ACTED_IN]->(m)
                    SET r.characters = rel.characters
                    """, {"rels": batch})
                else:
                    session.run("""
                    UNWIND $rels AS rel
                    MATCH (p:Person {id: rel.nconst})
                    MATCH (m:Movie {id: rel.tconst})
                    MERGE (p)-[r:RELATES_TO]->(m)
                    SET r.type = rel_type
                    """, {"rels": batch})

# ==============================
# PIPELINE
# ==============================
if __name__ == "__main__":
    df_movies = filter_top_movies("Data/Raw Data/title.basics.tsv", "Data/Raw Data/title.ratings.tsv")
    upload_movies(df_movies)

    df_people, df_principals = filter_people("Data/Raw Data/name.basics.tsv", "Data/Raw Data/title.principals.tsv", df_movies['tconst'].unique())
    upload_people(df_people)

    build_relationship_csvs(df_principals)
    upload_relationships()

    print("\n✅ Full ETL completed successfully.")