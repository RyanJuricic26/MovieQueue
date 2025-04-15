from Database.Neo4j_Connection import Connect
from neo4j.exceptions import TransientError
from collections import defaultdict
import streamlit as st

role_map = {
    "SHOT": "Cinematographer",
    "EDITED": "Editor",
    "CAST": "Casting Director",
    "PRODUCED": "Producer",
    "WROTE": "Writer",
    "DESIGNED PRODUCTION": "Production Designer",
    "FEATURED_IN_ARCHIVE_SOUND": "Archive Sound Contributor",
    "FEATURED_IN_ARCHIVE_FOOTAGE": "Archive Footage Contributor",
    "Designed Production": "Production Designer"
}


def get_candidate_movie_ids(user, genres):
    db = Connect()

    query = """
    MATCH (u:User {username: $user})-[r:RATED]->(m:Movie)
    WITH u, m, r.rating / 5.0 AS rating_weight

    MATCH (m)<-[rel]-(p:Person)
    WHERE type(rel) IN [
        'ACTED_IN', 'DIRECTED', 'WROTE', 'PRODUCED', 'COMPOSED_SCORE_FOR',
        'EDITED', 'SHOT', 'CAST', 'DESIGNED_PRODUCTION', 'ANIMATED'
    ]

    WITH u, p.name AS person_name, type(rel) AS role, rating_weight
    WITH u, role, person_name, SUM(rating_weight) AS influence

    WITH u, collect({person: person_name, role: role, weight: influence}) AS collaborators

    UNWIND collaborators AS wc
    MATCH (p:Person {name: wc.person})-[rel]->(rec:Movie)
    WHERE type(rel) = wc.role

    MATCH (rec)-[:HAS_GENRE]->(g:Genre)
    WHERE g.type IN $genres AND NOT EXISTS {
        MATCH (u)-[:RATED]->(rec)
    }

    WITH DISTINCT rec, collaborators
    WITH rec, collaborators ORDER BY rec.numVotes DESC
    LIMIT 75
    RETURN rec.tconst AS id, collaborators
    """

    try:
        results = db.run_query(query, {"user": user, "genres": genres})
        return [{"id": r["id"], "collaborators": r["collaborators"]} for r in results], False
    except TransientError as e:
        if "MemoryPoolOutOfMemoryError" in str(e):
            st.error("🚨 Too many matching movies for your selected genres. Try narrowing your genre selection.")
            return [], True
        else:
            raise


def get_scored_movies(ids, collaborators):
    db = Connect()

    query = """
    UNWIND $ids AS movieId
    MATCH (rec:Movie {tconst: movieId})
    WITH rec, rec.averageRating AS rec_rating, rec.numVotes AS rec_votes

    UNWIND $collaborators AS wc
    MATCH (p:Person {name: wc.person})-[rel]->(rec)
    WHERE type(rel) = wc.role

    WITH rec, wc, type(rel) AS role, rec_rating, rec_votes
    WITH rec, rec_rating, rec_votes,
         SUM(
            CASE role
                WHEN 'ACTED_IN' THEN 4.0
                WHEN 'DIRECTED' THEN 3.0
                WHEN 'WROTE' THEN 2.0
                WHEN 'PRODUCED' THEN 2.0
                WHEN 'COMPOSED_SCORE_FOR' THEN 2.0
                ELSE 1.0
            END * wc.weight
         ) AS total_collab_score

    WITH rec,
         total_collab_score,
         log(1 + rec.numVotes) AS popularity_score,
         rec.averageRating * 1.5 AS quality_score,
         total_collab_score + log(1 + rec.numVotes) + rec.averageRating * 1.5 AS total_score

    RETURN rec.tconst AS id, total_score
    ORDER BY total_score DESC
    """

    results = db.run_query(query, {"ids": ids, "collaborators": collaborators})
    return [{"id": r["id"], "score": r["total_score"]} for r in results]

def get_movie_details(ids):    
    db = Connect()

    query = """
    UNWIND $ids AS movieId
    MATCH (rec:Movie {tconst: movieId})
    OPTIONAL MATCH (rec)-[:HAS_GENRE]->(g:Genre)
    OPTIONAL MATCH (rec)<-[r]-(p:Person)
    WHERE type(r) IN [
        'ACTED_IN', 'DIRECTED', 'WROTE', 'PRODUCED', 'COMPOSED_SCORE_FOR',
        'EDITED', 'SHOT', 'CAST', 'DESIGNED_PRODUCTION', 'ANIMATED'
    ]
    WITH rec, collect(DISTINCT g.type) AS all_genres,
         collect(DISTINCT {name: p.name, role: type(r)}) AS collabs
    RETURN 
        rec.tconst AS id,
        rec.primaryTitle AS recommendation,
        rec.averageRating AS rec_rating,
        rec.numVotes AS rec_votes,
        rec.runtimeMinutes AS rec_runtime,
        rec.startYear AS rec_year,
        all_genres,
        [x IN collabs WHERE x.role = 'ACTED_IN' | x.name] AS shared_actors,
        [x IN collabs WHERE x.role = 'DIRECTED' | x.name] AS shared_directors,
        [x IN collabs WHERE x.role = 'COMPOSED_SCORE_FOR' | x.name] AS shared_composers,
        [x IN collabs WHERE x.role IN ['WROTE','PRODUCED','EDITED','SHOT','CAST','DESIGNED_PRODUCTION','ANIMATED'] | [x.name, x.role]] AS shared_others
    """

    results = db.run_query(query, {"ids": ids})

    return results
  
def format_recommendations(details, score_lookup, collab_lookup, genres):
    formatted_recommendations = []

    for rec in details:
        rec = dict(rec)
        rec["total_score"] = score_lookup.get(rec["id"], 0.0)

        seen_collabs = collab_lookup.get(rec["id"], [])
        seen_set = {(c["person"], c["role"]) for c in seen_collabs}

        # Filter down to shared people only
        rec["shared_actors"] = [name for name in rec["shared_actors"] if (name, "ACTED_IN") in seen_set]
        rec["shared_directors"] = [name for name in rec["shared_directors"] if (name, "DIRECTED") in seen_set]
        rec["shared_composers"] = [name for name in rec["shared_composers"] if (name, "COMPOSED_SCORE_FOR") in seen_set]
        rec["shared_others"] = [pair for pair in rec["shared_others"] if tuple(pair) in seen_set]

        formatted_recommendations.append(rec)


    return formatted_recommendations, False


def get_recommendations(user, genres):
    ids_and_collabs, memory_error = get_candidate_movie_ids(user, genres)
    if memory_error or not ids_and_collabs:
        return [], memory_error

    ids = [r["id"] for r in ids_and_collabs]
    collaborators = ids_and_collabs[0]["collaborators"] if ids_and_collabs else []

    scored = get_scored_movies(ids, collaborators)
    score_lookup = {r["id"]: r["score"] for r in scored}
    collab_lookup = {r["id"]: collaborators for r in scored}  # assuming same collabs for each

    details = get_movie_details([r["id"] for r in scored])
    formatted, _ = format_recommendations(details, score_lookup, collab_lookup, genres)
    return formatted, False
    
def display_recommendations(recommendations):
    if not recommendations:
        st.info("No recommendations found. Try rating more movies or selecting more genres.")
        return

    st.success("Here are your personalized recommendations:")

    for rec in recommendations:
        html_parts = []

        # --- Start Card ---
        html_parts.append("<div style='background:#1e1e1e;padding:20px;border-radius:16px;border:1px solid #444;margin-bottom:25px;box-shadow:0 4px 12px rgba(0,0,0,0.3);color:white;font-family:sans-serif;'>")

        # Title
        html_parts.append(f"<h2 style='margin-bottom:8px;'>🎬 {rec.get('recommendation')} <span style='font-size:0.7em; color:gray;'>({rec.get('rec_year')})</span></h2>")

        # genre tags
        all_genres = rec.get('all_genres') or rec.get('shared_genres') or []
        genre_tags = " ".join([
            f"<span style='background:#FF5C5C; color:white; padding:4px 8px; border-radius:8px; font-size:0.8em; margin-right:5px;'>{g}</span>"
            for g in all_genres
        ])

        html_parts.append(f"<div style='margin-bottom:8px;'>{genre_tags}</div>")

        # Info
        html_parts.append(f"<p style='margin:2px 0;'><strong>Runtime:</strong> {rec.get('rec_runtime')} mins</p>")
        html_parts.append(f"<p style='margin:2px 0;'><strong>Avg Rating:</strong> {round(rec.get('rec_rating')/2, 2)}/5 ⭐ | <strong>Votes:</strong> {rec.get('rec_votes'):,}</p>")
        html_parts.append(f"<p style='margin:2px 0;'><strong>Recommendation Score:</strong> <span style='color:#ffd700;'>{rec.get('total_score', 0.0):.2f}</span></p>")
        
        # Explanation Dropdown
        explanation_html = []
        explanation_html.append("""
        <details style='margin-top:15px;'>
            <summary style='cursor: pointer; font-weight:bold; font-size:1.05em; padding:4px 0;'>💡 Why was this recommended?</summary>
            <div style='margin-top:8px; transition: all 0.3s ease; line-height:1.6;'>
        """)

        if rec['shared_actors']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎭 Familiar Actors:</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec.get('shared_actors'))}</p>")

        if rec['shared_directors']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎬 Director(s):</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec.get('shared_directors'))}</p>")

        if rec['shared_composers']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎼 Composer(s):</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec.get('shared_composers'))}</p>")

        # Group other collaborators (excluding composers)
        crew_by_role = defaultdict(list)
        for name, role in rec['shared_others']:
            if role and role.upper() not in ["DIRECTED", "COMPOSED_MUSIC_FOR", "COMPOSER"]:                
                crew_by_role[role].append(name)

        if crew_by_role:
            explanation_html.append("<p style='margin:3px 0; font-weight:600;'>🛠 Other Collaborators:</p><ul style='margin:0 0 0 15px;padding:0;list-style:none;color:#ccc;'>")
            for role, people in sorted(crew_by_role.items()):
                readable_role = role_map.get(role, role.replace("_", " ").title())
                explanation_html.append(f"<li style='margin:2px 0;'>└ {readable_role}: {', '.join(sorted(people))}</li>")
            explanation_html.append("</ul>")

        explanation_html.append("</div></details>")
        html_parts.extend(explanation_html)

        # --- End Card ---
        html_parts.append("</div>")

        html = "".join(html_parts)
        st.markdown(html, unsafe_allow_html=True)

