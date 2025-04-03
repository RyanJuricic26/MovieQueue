import streamlit as st
from Modules.Menu import global_sidebar
from Modules.InitializeSessionStates import init_session_state
from Modules.RecommendMovies import get_recommendations, format_recommendations, display_recommendations
from Database.Neo4j_Connection import Connect

from Modules.auth import login_blocker

# protect the page
login_blocker()

st.set_page_config(page_title="Home", page_icon="🏡")


def show():
    st.title("📽 MovieQueue Home")
    st.write(f"Welcome back, **{st.session_state.username}**!")

    genre_query = """
    MATCH (g:Genre)
    RETURN DISTINCT g.name AS name
    ORDER BY name
    """
    db = Connect()

    genre_results = db.run_query(genre_query)
    genre_list = [g["name"] for g in genre_results]

    selected_genres = st.multiselect("🎯 Select Genres to Include in Recommendations:", genre_list)

    if selected_genres:
        raw_recommendations = get_recommendations(st.session_state.username, selected_genres)
        formatted = format_recommendations(raw_recommendations)
        display_recommendations(formatted)

init_session_state()    

show()

global_sidebar()