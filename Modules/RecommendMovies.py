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

}


def get_recommendations(user, genres):
    
    db = Connect()
    
    query = """
    MATCH (u:User {username: $user})-[r:RATED]->(m:Movie)
    WHERE r.rating >= 8

    // Collect user collaborators
    OPTIONAL MATCH (m)<-[:ACTED_IN]-(ua:Person)
    OPTIONAL MATCH (m)<-[:DIRECTED]-(ud:Person)
    OPTIONAL MATCH (m)<-[:COMPOSED_SCORE_FOR]-(uc:Person)
    OPTIONAL MATCH (m)<-[rel]-(uo:Person)
    WHERE type(rel) IN ['PRODUCED', 'EDITED', 'SHOT', 'CAST', 'DESIGNED_PRODUCTION', 'ANIMATED', 'WROTE']

    WITH u,
         COLLECT(DISTINCT ua) AS user_actors,
         COLLECT(DISTINCT ud) AS user_directors,
         COLLECT(DISTINCT uc) AS user_composers,
         COLLECT(DISTINCT uo) AS user_other_people,
         COLLECT(DISTINCT type(rel)) AS user_other_roles

    // Candidate movies (genre filter, but not based on user's history)
    MATCH (rec:Movie)
    WHERE NOT EXISTS { MATCH (u)-[:RATED]->(rec) }
      AND EXISTS {
          MATCH (rec)-[:HAS_GENRE]->(g2:Genre)
          WHERE g2.type IN $genres
      }

    // Match shared collaborators and genres
    OPTIONAL MATCH (rec)<-[:ACTED_IN]-(a)
    WHERE a IN user_actors
    OPTIONAL MATCH (rec)<-[:DIRECTED]-(d)
    WHERE d IN user_directors
    OPTIONAL MATCH (rec)<-[:COMPOSED_SCORE_FOR]-(c)
    WHERE c IN user_composers
    OPTIONAL MATCH (rec)<-[rto_rec]-(o)
    WHERE o IN user_other_people AND type(rto_rec) IN user_other_roles

    // Collect genres for scoring and display
    OPTIONAL MATCH (rec)-[:HAS_GENRE]->(g:Genre)
    WHERE g.type IN $genres
    OPTIONAL MATCH (rec)-[:HAS_GENRE]->(all_g:Genre)

    WITH rec,
         COLLECT(DISTINCT g.type) AS shared_genres,
         COLLECT(DISTINCT all_g.type) AS all_genres,
         COLLECT(DISTINCT a.name) AS shared_actors,
         COLLECT(DISTINCT d.name) AS shared_directors,
         COLLECT(DISTINCT c.name) AS shared_composers,
         COLLECT(DISTINCT [o.name, type(rto_rec)]) AS shared_others,
         rec.averageRating AS rec_rating,
         rec.numVotes AS rec_votes,
         rec.runtimeMinutes AS rec_runtime,
         rec.startYear AS rec_year

    WITH rec, shared_genres, all_genres, shared_actors, shared_directors, shared_composers, shared_others,
         rec_rating, rec_votes, rec_runtime, rec_year,
         SIZE(shared_genres) * 2 + SIZE(shared_actors) * 4 + SIZE(shared_directors) * 3 +
         SIZE(shared_composers) * 2 + SIZE(shared_others) * 1 +
         log(1 + rec_votes) * 2 + rec_rating * 2 AS total_score

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
        html_parts.append(f"<p style='margin:2px 0;'><strong>Avg Rating:</strong> {round(rec['rec_rating'], 2)}/10 ⭐ | <strong>Votes:</strong> {rec['rec_votes']:,}</p>")
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

