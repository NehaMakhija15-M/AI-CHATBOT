import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from services.db import run_query
from services.gemini import generate_sql, classify_intent, generate_greeting_reply, generate_explanation
from services.visual import show_visual
import streamlit.components.v1 as components

# Use session state to track which page to show
if "show_chatbot" not in st.session_state:
    st.session_state.show_chatbot = False

if not st.session_state.show_chatbot:
    st.set_page_config(page_title="Welcome", layout="wide")

    st.markdown("## 🤖 Welcome to the Chatbot Interface!")
    st.markdown("Click the robot icon below to open the Chatbot page.")

    # --- CSS for floating button ---
    st.markdown("""
        <style>
            .floating-button {
                position: fixed;
                width: 60px;
                height: 60px;
                bottom: 20px;
                left: 20px;
                background-color: #008CBA;
                color: white;
                border-radius: 50%;
                text-align: center;
                font-size: 30px;
                line-height: 60px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                z-index: 9999;
                cursor: pointer;
                text-decoration: none;
            }
            .floating-button:hover {
                background-color: #0079a1;
            }
        </style>
    """, unsafe_allow_html=True)

    # Use HTML for the floating button
    st.markdown(
        """
        <a href='/?show_chatbot=1' class='floating-button'>🤖</a>
        """,
        unsafe_allow_html=True
    )

    # Detect if the icon was clicked via query params (new API)
    query_params = st.query_params
    if query_params.get("show_chatbot", "0") == "1":
        st.session_state.show_chatbot = True
        st.query_params.clear()  # Clear all query params
        st.rerun()
else:
    st.set_page_config(page_title="SQL Chatbot", layout="wide")

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

                        user_query = user_query.lower().strip()

                        # Show pie if 'pie' in query, line if 'line', else bar
                        if "pie" in user_query:
                            chart_type = "pie"
                        elif "line" in user_query:
                            chart_type = "line"
                        else:
                            chart_type = "bar"

                        if df.shape[1] >= 1:
                            label_col = df.columns[0]
                            value_col = df.columns[1] if df.shape[1] > 1 else None

                            st.write(f"Label Column: `{label_col}`")
                            if value_col:
                                st.write(f"Value Column: `{value_col}`")

                            # Prepare chart data
                            if value_col and np.issubdtype(df[value_col].dtype, np.number):
                                chart_data = df.groupby(label_col)[value_col].sum().reset_index()
                            else:
                                chart_data = df.groupby(label_col).size().reset_index(name='Count')
                                value_col = 'Count'

                            if chart_type == "pie":
                                st.subheader("Pie Chart")
                                fig = px.pie(chart_data, names=label_col, values=value_col, title="Pie Chart")
                            elif chart_type == "line":
                                st.subheader("Line Chart")
                                fig = px.line(chart_data, x=label_col, y=value_col, title="Line Chart")
                            else:
                                st.subheader("Bar Chart")
                                fig = px.bar(chart_data, x=label_col, y=value_col, color=label_col, title="Bar Chart")

                            st.plotly_chart(fig)

                            st.subheader("Analysis")
                            st.write(generate_explanation(df))
                        else:
                            st.warning("Query returned insufficient columns for visualization.")
                    else:
                        st.warning("Query returned no data.")
                except Exception as e:
                    st.error("An error occurred:")
                    st.exception(e)
        else:
            st.warning("Sorry, I cannot convert this input into an SQL query.")
