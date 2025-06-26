import streamlit as st
import pandas as pd
from services.db import run_query
from services.gemini import generate_sql, classify_intent, generate_greeting_reply
from services.visual import show_visual
import re

st.title("Natural Language to Oracle SQL")

user_query = st.text_input("Ask your question (e.g. How many invoices this month?)")

if st.button("Run Query") and user_query:
    intent = classify_intent(user_query)
    if intent == "greeting":
        reply = generate_greeting_reply(user_query)
        st.success(reply)
    elif intent == "query":
        with st.spinner("Generating SQL..."):
            try:
                # Step 1: Generate SQL from user input
                sql = generate_sql(user_query)
                st.subheader("Generated SQL")
                st.code(sql, language="sql")

                # Step 2: Run SQL and get results
                df = run_query(sql)

                # Step 3: Check if data exists
                if not df.empty:
                    st.subheader("Query Result")
                    st.dataframe(df)

                    # Step 4: Visualize
                    show_visual(df)

                else:
                    st.warning("Query returned no data.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
    else:
        st.warning("Sorry, I cannot convert this input into an SQL query.")
