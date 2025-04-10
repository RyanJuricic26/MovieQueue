import streamlit as st
import plotly.express as px
from Modules.Menu import global_sidebar
from Modules.InitializeSessionStates import init_session_state
from Modules.GetAnalytics import get_analytics
from Modules.Analytics_Utils import safe_bar_chart, safe_metric

st.set_page_config(page_title="User Analytics", page_icon="📊")



def show():
    st.title("📊 Your Movie Taste in Data")

    user = st.session_state.get("username", None)
    
    if not user:
        st.warning("You must be logged in to view analytics.")
        st.stop()

    st.markdown(f"Welcome, **{user}**! Here’s what your movie watching habits reveal about you... 🎥📈")

    # Get analytics data
    total_ratings, avg_rating, rating_dist_df, genre_df, most_disagreed = get_analytics(user)

    # 🎯 Summary stats
    st.subheader("🎯 Your Stats at a Glance")
    col1, col2 = st.columns(2)
    with col1:
        safe_metric("🎬 Total Ratings", total_ratings)
    with col2:
        safe_metric("⭐ Average Rating", f"{avg_rating:.2f}" if avg_rating else "N/A")

    # 📊 Rating Distribution
    if not rating_dist_df.empty:
        st.subheader("⭐ How You Rate Movies")

        st.caption("From low to high – where do your most common ratings land?")
        safe_bar_chart(rating_dist_df, "rating", "count")
    else:
        st.info("You haven’t rated any movies yet!")

    # 🎭 Genre Breakdown
    if not genre_df.empty:
        st.subheader("🎭 Your Favorite Genres")

        st.caption("Genres you've watched most often:")
        safe_bar_chart(genre_df, "genre", "count", "Most Watched Genres")

        st.caption("And the genres you tend to rate highest:")
        safe_bar_chart(genre_df, "genre", "avg_rating", "Average Rating by Genre")
    else:
        st.info("Genre data will appear once you’ve rated some movies!")

    # 🧐 Rating Disagreement Insight
    if most_disagreed:
        st.subheader("🤔 Where You Disagreed Most")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{most_disagreed['title']}** ({most_disagreed['year']})")
            st.caption("You saw it very differently from the rest of the world.")
        with col2:
            st.metric("Your Rating", most_disagreed["user_rating"])
            st.metric("Avg Rating", f"{most_disagreed['avg_rating']:.2f}")
            st.metric("Disparity", f"{most_disagreed['diff']:.2f}")
    else:
        st.info("No rating disparity info yet.")

init_session_state()

show()

global_sidebar()

