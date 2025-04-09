import streamlit as st
from Modules.auth import init_session_state
from Modules.Menu import global_sidebar

st.set_page_config(page_title="MovieQueue | Welcome", page_icon="🎬", layout="wide")


# ------------------------
# Session Initialization
# ------------------------
init_session_state()
global_sidebar()

# ------------------------
# Public Home Page Content
# ------------------------

st.title("🍿 Welcome to MovieQueue")
st.markdown("""
### Your Personalized Movie Recommendation System
MovieQueue helps you:

- 🎯 Discover movies you'll love, powered by **Neo4j's Graph Database**.
- ⭐ Rate movies and improve your future recommendations.
- 📊 Track your movie-watching history with analytics.
- 🧑‍💻 Share your activity and see what your friends are watching.

---

👉 To get started, create an account or login using the sidebar.
""")

if st.session_state.logged_in:
    st.success(f"✅ You are logged in as `{st.session_state.username}` — use the sidebar to navigate the app.")
else:
    st.info("🔐 Please login or register to unlock recommendations and analytics.")
