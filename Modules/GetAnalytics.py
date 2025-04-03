from Modules.Analytics_Utils import records_to_df
from Database.Neo4j_Connection import Connect

def get_analytics(user):

    db = Connect()

    params = {"user": user}

    queries = {
        "total_ratings": "MATCH (u:User {username: $user})-[:RATED]->(m:Movie) RETURN count(*) AS total_ratings",
        "avg_rating": "MATCH (u:User {username: $user})-[r:RATED]->(m:Movie) RETURN avg(r.rating) AS avg_rating",
        "rating_dist": "MATCH (u:User {username: $user})-[r:RATED]->(m:Movie) RETURN r.rating AS rating, count(*) AS count ORDER BY rating",
        "genre_dist": "MATCH (u:User {username: $user})-[r:RATED]->(m:Movie)-[:HAS_GENRE]->(g:Genre) RETURN g.name AS genre, count(*) AS count, avg(r.rating) AS avg_rating ORDER BY count DESC"
    }

    results = {key: db.run_query(query, params) for key, query in queries.items()}
    results_df = {key: records_to_df(res) for key, res in results.items()}

    # Extract scalars
    total_ratings = results_df["total_ratings"].iloc[0, 0] if not results_df["total_ratings"].empty else 0
    avg_rating = results_df["avg_rating"].iloc[0, 0] if not results_df["avg_rating"].empty else None

    return total_ratings, avg_rating, results_df["rating_dist"], results_df["genre_dist"]