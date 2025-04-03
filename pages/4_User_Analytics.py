import streamlit as st
import plotly.express as px
from Modules.Menu import global_sidebar
from Modules.InitializeSessionStates import init_session_state
from Modules.GetAnalytics import get_analytics
from Modules.Analytics_Utils import safe_bar_chart, safe_metric

st.set_page_config(page_title="User Analytics", page_icon="📊")



def show():
    st.title("🎬 User Analytics")

    user = st.session_state.username
    
    if user is None:
        st.warning("You must be logged in to view analytics.")
        st.stop()

   
    total_ratings, avg_rating, rating_dist_df, genre_df = get_analytics(user)

    st.header("General Stats")
    safe_metric("Total Ratings", total_ratings)
    safe_metric("Average Rating", avg_rating)

    st.header("Rating Distribution")
    if not rating_dist_df.empty:
        st.bar_chart(rating_dist_df.set_index("rating")["count"])
    else:
        st.info("No ratings yet.")

    safe_bar_chart(genre_df, "genre", "count", "Most Rated Genres")
    safe_bar_chart(genre_df, "genre", "avg_rating", "Average Rating by Genre")


init_session_state()

show()

global_sidebar()

