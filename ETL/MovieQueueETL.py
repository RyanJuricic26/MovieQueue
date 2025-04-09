import pandas as pd
import ast
from tqdm import tqdm
from collections import defaultdict
from ETL_config import BATCH_SIZE, TOP_K, MOVIE_DATA_PATH, RATINGS_DATA_PATH, PEOPLE_DATA_PATH, PRINCIPALS_DATA_PATH, REL_OUTPUT_DIR, DTYPE_BASICS, DTYPE_RATINGS, DTYPE_NAMES, DTYPE_PRINCIPALS, PROFESSION_TO_RELATIONSHIP
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Database.Neo4j_Connection import Connect

os.makedirs(REL_OUTPUT_DIR, exist_ok=True)

# ==============================
# READ TSV FILES
# ==============================
def read_data(path, dtype):
    return pd.read_csv(path, delimiter='\t', dtype=dtype, na_values='\\N')

# ==============================
# FILTER MOVIES
# ==============================
def filter_top_movies(movie_csv, rating_csv, DTYPE_BASICS, DTYPE_RATINGS):
    print("\n[STEP 1] Filtering Movies...")

    df = read_data(movie_csv, DTYPE_BASICS)
    ratings = read_data(rating_csv, DTYPE_RATINGS)
    df = df[df['titleType'] == 'movie']

    merged_data = df.merge(ratings, how='left', on='tconst')

    merged_data['numVotes'] = pd.to_numeric(merged_data['numVotes'], errors='coerce')
    merged_data = merged_data.dropna(subset=['numVotes'])
    merged_data['numVotes'] = merged_data['numVotes'].astype(int)

    merged_data['genres'] = merged_data['genres'].fillna("").apply(lambda x: x.split(",") if x else [])
    
    # Treat isAdult as a genre
    merged_data.loc[merged_data['isAdult'] == 1, 'genres'] = merged_data.loc[merged_data['isAdult'] == 1, 'genres'].apply(lambda g: g + ['Adult'])

    df_exploded = merged_data.explode('genres')

    top_movies = df_exploded.groupby('genres', group_keys=False).apply(lambda x: x.nlargest(TOP_K, 'numVotes'))
    top_movies = top_movies.drop_duplicates('tconst')

    print(f"[INFO] Filtered down to {len(top_movies)} top movies.")
    return top_movies

# ==============================
# UPLOAD MOVIES
# ==============================
def upload_movies(df, db):
    print("\n[STEP 2] Uploading Movies...")

    with db.driver.session() as session:
        for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Uploading Movies"):
            batch = df.iloc[i:i+BATCH_SIZE].to_dict(orient="records")
            session.run("""
            UNWIND $movies AS movie
            MERGE (m:Movie {tconst: movie.tconst})
            ON CREATE SET
                m.primaryTitle = movie.primaryTitle,
                m.startYear = toInteger(movie.startYear),
                m.runtimeMinutes = CASE WHEN movie.runtimeMinutes=\"\\N\" THEN NULL ELSE toInteger(movie.runtimeMinutes) END,
                m.averageRating = CASE WHEN movie.averageRating=\"\\N\" THEN NULL ELSE toFloat(movie.averageRating) END,
                m.numVotes = movie.numVotes

            FOREACH (genre IN movie.genres |
                MERGE (g:Genre {type: genre})
                MERGE (m)-[:HAS_GENRE]->(g)
            )
            """, {"movies": batch})

    print(f"[INFO] Finished Movies Upload.")

# ==============================
# FILTER PEOPLE
# ==============================
def filter_people(people_csv, principals_csv, valid_movie_ids, DTYPE_NAMES, DTYPE_PRINCIPALS):
    print("\n[STEP 3] Filtering People...")

    
    df_p = read_data(principals_csv, DTYPE_PRINCIPALS)
    df_p = df_p[df_p['tconst'].isin(valid_movie_ids)]

    involved_people = set(df_p['nconst'].unique())

    df_people = read_data(people_csv, DTYPE_NAMES)
    df_people = df_people[df_people['nconst'].isin(involved_people)]

    print(f"[INFO] Filtered down to {len(df_people)} people.")

    return df_people, df_p

# ==============================
# UPLOAD PEOPLE
# ==============================
def upload_people(df, db):
    print("\n[STEP 4] Uploading People...")

    df["birthYear"] = df["birthYear"].fillna("0").astype(int)
    df["deathYear"] = df["deathYear"].fillna("0").astype(int)
    df["primaryProfession"] = df["primaryProfession"].apply(lambda x: x.split(",") if pd.notna(x) else [])

    with db.driver.session() as session:
        for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Uploading People"):
            batch = df.iloc[i:i+BATCH_SIZE].to_dict(orient="records")
            session.run("""
            UNWIND $people AS person
            MERGE (p:Person {nconst: person.nconst})
            ON CREATE SET
                p.name = person.primaryName,
                p.birthYear = CASE WHEN person.birthYear=0 THEN NULL ELSE person.birthYear END,
                p.deathYear = CASE WHEN person.deathYear=0 THEN NULL ELSE person.deathYear END

            FOREACH (prof IN person.primaryProfession |
                MERGE (pr:Profession {type: prof})
                MERGE (p)-[:HAS_PROFESSION]->(pr)
            )
            """, {"people": batch})

    print(f"[INFO] Finished People Upload.")

# ==============================
# FILTER RELATIONSHIPS
# ==============================
def filter_relationships(df_principals):
    print("\n[STEP 5] Filtering People -> Movie Relationships...")

    relationship_map = defaultdict(list)

    for _, row in df_principals.iterrows():
        tconst = row['tconst']
        nconst = row['nconst']
        category = row.get('category', '')
        job = row.get('job', '')

        rel_type = None

        if pd.notna(category) and category.lower() in PROFESSION_TO_RELATIONSHIP:
            rel_type = PROFESSION_TO_RELATIONSHIP[category.lower()]
        elif pd.notna(job) and job.lower() in PROFESSION_TO_RELATIONSHIP:
            rel_type = PROFESSION_TO_RELATIONSHIP[job.lower()]
        else:
            continue  # skip unknown/unsupported types

        if rel_type == "ACTED_IN":
            characters = row.get('characters', '')
            relationship_map[rel_type].append({
                'tconst': tconst,
                'nconst': nconst,
                'characters': characters if pd.notna(characters) else ""
            })
        else:
            relationship_map[rel_type].append({
                'tconst': tconst,
                'nconst': nconst
            })

    print(f"[INFO] Finished Filtering People -> Movie Relationships.")
    return relationship_map

# ==============================
# UPLOAD RELATIONSHIP 
# ==============================
def upload_relationships(relationship_map, db):
    print("\n[STEP 6] Uploading People -> Movie Relationships...")

    with db.driver.session() as session:
        for rel_type, rows in relationship_map.items():
            print(f"[INFO] Uploading {rel_type} relationships ({len(rows)} entries)...")

            for i in range(0, len(rows), 500):  # batch in chunks
                chunk = rows[i:i+500]

                if rel_type == "ACTED_IN":
                    session.run(f"""
                        UNWIND $rows AS row
                        MATCH (p:Person {{nconst: row.nconst}})
                        MATCH (m:Movie {{tconst: row.tconst}})
                        MERGE (p)-[r:{rel_type}]->(m)
                        SET r.characters = row.characters
                    """, parameters={'rows': chunk})
                else:
                    session.run(f"""
                        UNWIND $rows AS row
                        MATCH (p:Person {{nconst: row.nconst}})
                        MATCH (m:Movie {{tconst: row.tconst}})
                        MERGE (p)-[:{rel_type}]->(m)
                    """, parameters={'rows': chunk})

    print(f"[INFO] Finished Uploading People -> Movie Relationships.")



# ==============================
# PIPELINE
# ==============================
if __name__ == "__main__":
    print("Starting ETL Script...")

    db = Connect()

    df_movies = filter_top_movies(MOVIE_DATA_PATH, RATINGS_DATA_PATH, DTYPE_BASICS, DTYPE_RATINGS)
    upload_movies(df_movies, db)

    df_people, df_principals = filter_people(PEOPLE_DATA_PATH, PRINCIPALS_DATA_PATH, df_movies['tconst'].unique(), DTYPE_NAMES, DTYPE_PRINCIPALS)
    upload_people(df_people, db)

    relationship_map = filter_relationships(df_principals)    
    upload_relationships(relationship_map, db)

    print("\n✅ Full ETL completed successfully.")