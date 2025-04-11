from Database.Neo4j_Connection import Connect
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


def get_recommendations(user, genres):
    
    db = Connect()
    
    query = """
    MATCH (u:User {username: $user})-[r:RATED]->(m:Movie)
    WITH u, m, r.rating / 5.0 AS rating_weight

    OPTIONAL MATCH (m)-[:HAS_GENRE]->(g:Genre)
    WITH u, m, rating_weight, collect(DISTINCT g.type) AS user_genres

    OPTIONAL MATCH (m)<-[rel]-(p:Person)
    WHERE type(rel) IN [
        'ACTED_IN', 'DIRECTED', 'WROTE', 'PRODUCED', 'COMPOSED_SCORE_FOR',
        'EDITED', 'SHOT', 'CAST', 'DESIGNED_PRODUCTION', 'ANIMATED'
    ]
    WITH u, user_genres, p.name AS person_name, type(rel) AS role, rating_weight
    WHERE person_name IS NOT NULL
    WITH u, user_genres, role, person_name, SUM(rating_weight) AS influence
    WITH u, user_genres, collect({person: person_name, role: role, weight: influence}) AS weighted_collaborators

    MATCH (rec:Movie)-[:HAS_GENRE]->(rg:Genre)
    WHERE rg.type IN $genres AND NOT EXISTS { MATCH (u)-[:RATED]->(rec) }

    OPTIONAL MATCH (rec)-[:HAS_GENRE]->(rg_all:Genre)
    OPTIONAL MATCH (rec)<-[rel2]-(collab:Person)
    WHERE type(rel2) IN [
        'ACTED_IN', 'DIRECTED', 'WROTE', 'PRODUCED', 'COMPOSED_SCORE_FOR',
        'EDITED', 'SHOT', 'CAST', 'DESIGNED_PRODUCTION', 'ANIMATED'
    ]

    WITH rec, collect(DISTINCT rg_all.type) AS all_genres,
         collect(DISTINCT rg_all.type) FILTER (WHERE rg_all.type IN $genres) AS shared_genres,
         collect(DISTINCT {name: collab.name, role: type(rel2)}) AS rec_collaborators,
         rec.averageRating AS rec_rating,
         rec.numVotes AS rec_votes,
         rec.runtimeMinutes AS rec_runtime,
         rec.startYear AS rec_year,
         u, weighted_collaborators

    WITH rec, all_genres, shared_genres, rec_rating, rec_votes, rec_runtime, rec_year,
         [collab IN rec_collaborators |
            REDUCE(s = 0.0,
                x IN [x IN weighted_collaborators WHERE x.person = collab.name AND x.role = collab.role] |
                s + (
                    CASE collab.role
                        WHEN 'ACTED_IN' THEN 4.0
                        WHEN 'DIRECTED' THEN 3.0
                        WHEN 'WROTE' THEN 2.0
                        WHEN 'PRODUCED' THEN 2.0
                        WHEN 'COMPOSED_SCORE_FOR' THEN 2.0
                        ELSE 1.0
                    END * x.weight
                )
            )
         ] AS collaborator_scores,
         [collab.name WHERE collab.role = 'ACTED_IN'] AS shared_actors,
         [collab.name WHERE collab.role = 'DIRECTED'] AS shared_directors,
         [collab.name WHERE collab.role = 'COMPOSED_SCORE_FOR'] AS shared_composers,
         [ [collab.name, collab.role] WHERE collab.role IN ['WROTE','PRODUCED','EDITED','SHOT','CAST','DESIGNED_PRODUCTION','ANIMATED'] ] AS shared_others

    WITH rec, all_genres, shared_genres, shared_actors, shared_directors, shared_composers, shared_others,
         rec_rating, rec_votes, rec_runtime, rec_year,
         REDUCE(total = 0.0, s IN collaborator_scores | total + s) AS total_collab_score,
         log(1 + rec_votes) * 1.0 AS popularity_score,
         rec_rating * 1.5 AS quality_score

    WITH rec, all_genres, shared_genres, shared_actors, shared_directors, shared_composers, shared_others,
         rec_rating, rec_votes, rec_runtime, rec_year,
         total_collab_score, popularity_score, quality_score,
         SIZE(shared_genres) * 1.0 + total_collab_score + popularity_score + quality_score AS total_score

    ORDER BY total_score DESC
    LIMIT 10

    RETURN rec.primaryTitle AS recommendation,
           rec.id AS id,
           all_genres,
           shared_genres,
           shared_actors,
           shared_directors,
           shared_composers,
           shared_others,
           rec_rating,
           rec_votes,
           rec_runtime,
           rec_year,
           total_score
    """

    recommendations = db.run_query(query, {"user": user, "genres": genres})

    formatted_recommendations = []

    for rec in recommendations:
        rec = dict(rec)

        explanation = []
        if rec['shared_genres']:
            explanation.append(f"Shares {len(rec['shared_genres'])} genre(s): {', '.join(rec['shared_genres'])}")
        if rec['shared_actors']:
            explanation.append(f"Has {len(rec['shared_actors'])} actor(s) you know: {', '.join(rec['shared_actors'])}")
        if rec['shared_directors']:
            explanation.append(f"Shares director(s): {', '.join(rec['shared_directors'])}")
        if rec['shared_composers']:
            explanation.append(f"Shares composer(s): {', '.join(rec['shared_composers'])}")

        # Remove duplicates and format others with roles
        primary_people = set(rec['shared_actors']) | set(rec['shared_directors']) | set(rec['shared_composers'])
        unique_others = [f"{name} ({role})" for name, role in rec['shared_others'] if name not in primary_people]

        if unique_others:
            explanation.append(f"Includes other familiar collaborators: {', '.join(sorted(unique_others))}")

        rec['explanation'] = "<br>".join(explanation) if explanation else "Has matching genres or collaborators."
        formatted_recommendations.append(rec)

    return formatted_recommendations



def format_recommendations(recommendations):
    formatted = []

    for rec in recommendations:
        rec = dict(rec)
        explanation = []

        if rec['shared_genres']:
            explanation.append(f"Shares {len(rec['shared_genres'])} genre(s): {', '.join(rec['shared_genres'])}")
        if rec['shared_actors']:
            explanation.append(f"Has {len(rec['shared_actors'])} actor(s) you know: {', '.join(rec['shared_actors'])}")
        if rec['shared_directors']:
            explanation.append(f"Shares director(s): {', '.join(rec['shared_directors'])}")
        if rec['shared_composers']:
            explanation.append(f"Shares composer(s): {', '.join(rec['shared_composers'])}")

        # ------- Group other collaborators by role -------
        primary_people = set(rec['shared_actors']) | set(rec['shared_directors']) | set(rec['shared_composers'])
        grouped_others = defaultdict(list)

        for name, role in rec['shared_others']:
            if name is None or role is None:
                continue
            if name not in primary_people:
                grouped_others[role].append(name)

        for role, people in grouped_others.items():
            if people:
                readable_role = role_map.get(role, role.replace("_", " ").title())
                explanation.append(f"Shares {readable_role}(s): {', '.join(sorted(people))}")

        rec['explanation'] = "<br>".join(explanation) if explanation else "Has matching genres or collaborators."
        formatted.append(rec)

    return formatted



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
        html_parts.append(f"<h2 style='margin-bottom:8px;'>🎬 {rec['recommendation']} <span style='font-size:0.7em; color:gray;'>({rec['rec_year']})</span></h2>")

        # genre tags
        all_genres = rec.get('all_genres', rec['shared_genres'])
        genre_tags = " ".join([
            f"<span style='background:#FF5C5C; color:white; padding:4px 8px; border-radius:8px; font-size:0.8em; margin-right:5px;'>{g}</span>"
            for g in all_genres
        ])

        html_parts.append(f"<div style='margin-bottom:8px;'>{genre_tags}</div>")

        # Info
        html_parts.append(f"<p style='margin:2px 0;'><strong>Runtime:</strong> {rec['rec_runtime']} mins</p>")
        html_parts.append(f"<p style='margin:2px 0;'><strong>Avg Rating:</strong> {round(rec['rec_rating']/2, 2)}/5 ⭐ | <strong>Votes:</strong> {rec['rec_votes']:,}</p>")
        html_parts.append(f"<p style='margin:2px 0;'><strong>Recommendation Score:</strong> <span style='color:#ffd700;'>{rec['total_score']:.2f}</span></p>")

        # Explanation Dropdown
        explanation_html = []
        explanation_html.append("""
        <details style='margin-top:15px;'>
            <summary style='cursor: pointer; font-weight:bold; font-size:1.05em; padding:4px 0;'>💡 Why was this recommended?</summary>
            <div style='margin-top:8px; transition: all 0.3s ease; line-height:1.6;'>
        """)

        if rec['shared_actors']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎭 Familiar Actors:</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec['shared_actors'])}</p>")

        if rec['shared_directors']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎬 Director(s):</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec['shared_directors'])}</p>")

        if rec['shared_composers']:
            explanation_html.append(f"<p style='margin:3px 0; font-weight:600;'>🎼 Composer(s):</p><p style='margin-left:12px; color:#ccc;'>{', '.join(rec['shared_composers'])}</p>")

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

