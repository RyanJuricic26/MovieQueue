from neo4j import GraphDatabase
import streamlit as st
from dotenv import load_dotenv
import os


# Neo4j Database Connection
class Neo4jConnection:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))  # drop the underscore
        except Exception as e:
            st.error(f"❌ Neo4j Connection Error: {e}")

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record for record in result]


def Connect():
    # Connect to Neo4j (Replace with your credentials)
    load_dotenv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    db = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    return db