import streamlit as st
import bcrypt
from Database.Neo4j_Connection import Connect


def create_user(username, password, db):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with db.driver.session() as session:
        session.run("CREATE (u:User {username: $username, password: $password})",
                    username=username, password=hashed)

def verify_user(username, password, db):
    with db.driver.session() as session:
        result = session.run("MATCH (u:User {username: $username}) RETURN u.password AS password",
                             username=username)
        record = result.single()
        if record:
            stored_hash = record["password"]
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        return False

def user_exists(username, db):
    with db.driver.session() as session:
        result = session.run("MATCH (u:User {username: $username}) RETURN u", username=username)
        return result.single() is not None

def login_blocker():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.warning("You must login to access this page.")
        show_login()
        st.stop()

def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

def show_login():

    db = Connect()

    # Setup toggle
    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    # ---------- LOGIN FORM ----------
    if not st.session_state.show_register:
        with st.form("login_form"):
            st.subheader("🔐 Login")

            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")

            submitted = st.form_submit_button("🚪 Login")

            if submitted:
                if verify_user(username, password, db):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("✅ Login successful! Use the sidebar to navigate.")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

        # ✅ Instant switch button (fixes the double-click problem)
        st.button("Don't have an account? Click here to Register", on_click=lambda: st.session_state.update(show_register=True))


    # ---------- REGISTER FORM ----------
    else:
        with st.form("register_form"):
            st.subheader("🟣 Register")

            username = st.text_input("👤 Choose a Username")
            password = st.text_input("🔑 Choose a Password", type="password")
            password_confirm = st.text_input("🔑 Confirm Password", type="password")

            submitted = st.form_submit_button("🟣 Create Account")

            if submitted:
                if password != password_confirm:
                    st.error("❌ Passwords do not match.")
                elif len(password) < 4:
                    st.warning("⚠ Password should be at least 4 characters.")  # optional
                elif not user_exists(username, db):
                    create_user(username, password, db)
                    st.success("🎉 Account created! You can now login.")
                    st.session_state.show_register = False  # Return to login form
                else:
                    st.warning("⚠ Username already exists.")

        # ✅ Instant switch back to login
        st.button("Already have an account? Click here to Login", on_click=lambda: st.session_state.update(show_register=False))
