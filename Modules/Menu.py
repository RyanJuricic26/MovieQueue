import streamlit as st


def global_sidebar():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    st.sidebar.title("🎬 MovieQueue")

    if st.session_state.logged_in:
        # Full navigation for logged-in users
        st.sidebar.markdown(f"👤 Logged in as `{st.session_state.username}`")

        st.sidebar.page_link("pages/2_Recommendations.py", label="Recommendations", icon="🎥")
        st.sidebar.page_link("pages/3_Rate_Movies.py", label="Rate Movies", icon="🎬")
        st.sidebar.page_link("pages/4_User_Analytics.py", label="User Analytics", icon="📊")

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    else:
        # Only show Login/Register page if not logged in
        st.sidebar.page_link("MovieQueue.py", label="Home", icon="🏡")
        st.sidebar.page_link("pages/1_Login.py", label="Login / Register", icon="🔐")