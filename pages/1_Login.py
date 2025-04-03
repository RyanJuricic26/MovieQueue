import streamlit as st
from Modules.auth import show_login
from Modules.Menu import global_sidebar

st.set_page_config(page_title="Login", page_icon="🔐")


st.title("🔐 Login to MovieQueue")

# Just show the login form
show_login()
global_sidebar()

# Optional
if st.session_state.get("logged_in", False):
    st.success("You're already logged in! Use the sidebar to go to other pages.")