import streamlit as st
from Modules.Menu import global_sidebar
from Modules.InitializeSessionStates import init_session_state
from Database.Neo4j_Connection import Connect
import datetime
import pandas as pd

st.set_page_config(page_title="Rate Movies", page_icon="🎬")


def show():
    # ---------- Settings ----------
    discovery_methods = [
        "Recommended by Friend",
        "Recommended by MovieQueue",
        "Recommended by Streaming Service",
        "Online Advertising",
        "Social Media",
        "Other"
    ]

    # ---------- Star Rating Choices ----------
    stars = [f"{i/2} ⭐" for i in range(1, 11)]  # 0.5 to 5

    # ---------- UI ----------
    st.title("⭐ Rate a Movie")
    st.write("Search for a movie you've watched and tell us what you think!")

    # ---------- Database Connection ----------
    db = Connect()

    # ---------- Autocomplete Search ----------
    st.subheader("Search Movie")

    movie_query = """
    MATCH (m:Movie)
    OPTIONAL MATCH (m)-[:HAS_GENRE]->(g:Genre)
    WITH m, collect(DISTINCT g.type) AS genres
    RETURN m.tconst AS tconst, m.primaryTitle AS title, m.startYear AS year, m.runtimeMinutes AS runtime, m.averageRating AS rating, genres
    ORDER BY m.primaryTitle
    """

    movies = db.run_query(movie_query)
    movies = [dict(movie) for movie in movies]

    movie_options = {f"{m['title']} ({m['year']})": m for m in movies}
    selected_title = st.selectbox("Select Movie", [""] + list(movie_options.keys()))

    # ---------- Movie Info ----------
    if selected_title and selected_title in movie_options:
        movie = movie_options[selected_title]

        with st.container():
            st.markdown("---")
            st.subheader(f"{movie['title']} ({movie['year']})")
            st.markdown(f"**Runtime:** {movie['runtime']} mins | **Avg Rating:** {round(movie['rating']/2, 2)}/5")
            genre_tags = " ".join([
                f"<span style='background:#FF5C5C; color:white; padding:4px 8px; border-radius:8px; font-size:0.8em; margin-right:5px;'>{g}</span>"
                for g in movie['genres']
            ])
            st.markdown(f"Genres: {genre_tags}", unsafe_allow_html=True)

            # Check if user already rated this
            existing_rating_query = "MATCH (u:User {username: $user})-[r:RATED]->(m:Movie {tconst: $tconst}) RETURN r.rating AS rating"
            existing = db.run_query(existing_rating_query, {"user": st.session_state.username, "tconst": movie['tconst']})

            if existing:
                st.warning(f"You have already rated this movie: {existing[0]['rating']}/5")

            # ---------- Watch Details ----------
            st.subheader("Watch Information")
            discovery = st.selectbox("How did you discover this movie?", discovery_methods)
            watch_date = st.date_input("Date Watched", datetime.date.today())
            watch_time = st.time_input("Time Watched", pd.to_datetime('20:00'))

            # ---------- Star Rating ----------
            st.subheader("Your Rating")
            rating_label = st.select_slider("Select your rating (supports half-stars)", options=stars)
            rating = float(rating_label.split(" ")[0])

            # ---------- Submit ----------
            if st.button("Submit Rating"):
                db.run_query("""
                    MERGE (u:User {username: $user})
                    WITH u
                    MATCH (m:Movie {tconst: $tconst})
                    MERGE (u)-[r:RATED]->(m)
                    SET r.rating = $rating,
                        r.discovery = $discovery,
                        r.date = date($date),
                        r.time = time($time)
                    """, {
                        "user": st.session_state.username,
                        "tconst": movie['tconst'],
                        "rating": rating,
                        "discovery": discovery,
                        "date": watch_date.isoformat(),
                        "time": watch_time.isoformat()
                    })

                st.success("✅ Rating submitted!")
                st.rerun()

    else:
        st.info("Please select a movie to continue.")



init_session_state()    

show()

global_sidebar()

