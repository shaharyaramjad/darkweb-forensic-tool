import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import pandas as pd

# Load .env
load_dotenv()

# Connection config
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

st.title("🧑‍💻 SQL Query Interface")

# Query input
query = st.text_area("Write your SQL query here:", height=200)

if st.button("Run Query"):
    if not query.strip():
        st.warning("⚠️ Please enter a query before running.")
    else:
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            cursor.execute(query)

            # Fetch results if SELECT query
            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                columns = cursor.column_names
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df)
            else:
                conn.commit()
                st.success("✅ Query executed successfully (non-select).")

            cursor.close()
            conn.close()

        except mysql.connector.Error as e:
            st.error(f"❌ MySQL Error: {e}")
