# ── IMPORTS ──
import os
import json
from groq import Groq
import streamlit as st
from dotenv import load_dotenv

# ── LOAD ENV ──
# Reads .env file and loads Groq_API key into environment
load_dotenv()
api_key = os.getenv("Groq_API")

# ── PAGE CONFIG ──
# sets browser tab title and icon
st.set_page_config(
    page_title="Text-to-SQL Generator",
    page_icon="🗄️",
    layout="centered"
)

# ── TITLE & DESCRIPTION ──
st.title("🗄️ Text-to-SQL Generator")
st.caption("Type a plain English question → get a SQL query instantly")
st.divider()

# ── CHECK API KEY ──
# Stop app immediately if API key is missing — nothing works without it
if not api_key:
    st.error("GROQ_API key not found. Please add it to your .env file.")
    st.stop()

# ── GROQ CLIENT ──
# Instantiate once — reused across all API calls
client = Groq(api_key=api_key)

# ── SYSTEM PROMPT ──
# Builds the instruction sent to the LLM
# Injects schema and question dynamically into the prompt
def build_prompt(schema, question):
    return f"""You are a SQL expert. Convert the natural language question into a SQL query based ONLY on the provided schema.

DATABASE CONTEXT:
{schema}

QUESTION:
{question}

RULES:
1. Use ONLY tables and columns explicitly listed in the schema. Never invent columns or tables.
2. Always list EVERY condition applied in plain English in conditions_applied
   (e.g. "Age filter: users older than 25", "Status filter: only active users").
3. If any term is ambiguous or undefined (like "recent", "popular", "top"),
   add a conditions_applied entry formatted as "UNCLEAR: <reason>".
4. If the schema is missing details needed to answer the question,
   set sql_query to "-- Cannot generate: missing schema details" and explain why.
5. Never leave conditions_applied empty if a WHERE clause exists in the query.
6. Return ONLY valid JSON — no markdown, no backticks, no extra text.

Return this exact JSON:
{{
  "sql_query": "string",
  "explanation": "string",
  "tables_used": ["string"],
  "conditions_applied": ["string"]
}}"""

# ── GROQ API CALL ──
# Sends the prompt to Groq and returns parsed JSON result as a Python dictionary
def generate_sql(schema, question):
    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # Groq model
        temperature=0.1,                 # low = accurate and consistent, not creative
        messages=[
            {
                "role": "system",        # sets global behavior of the AI
                "content": "You are a SQL expert. Always respond with valid JSON only. No markdown, no backticks, no extra text."
            },
            {
                "role": "user",          # actual prompt with schema + question
                "content": build_prompt(schema, question)
            }
        ]
    )

    # Extract raw text from Groq's response
    raw_text = chat_completion.choices[0].message.content

    # Safety cleanup — remove backticks if model accidentally adds them
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    # Convert JSON string → Python dictionary so we can use result["sql_query"] etc.
    return json.loads(raw_text)

# ── INPUT FIELDS ──
st.subheader("Your Input")

# Multi-line input for database schema — users paste their table structure here
schema = st.text_area(
    "Database Schema",
    placeholder="e.g. Table users(id, name, age, city)",
    height=100
)

# Single-line input for the plain English question
question = st.text_input(
    "Your Question",
    placeholder="e.g. Show all users older than 25"
)

st.divider()

# ── GENERATE BUTTON ──
if st.button("Generate SQL", use_container_width=True, type="primary"):

    # Validate inputs — .strip() removes extra spaces before checking if empty
    if not schema.strip():
        st.warning("Please enter a database schema.")
    elif not question.strip():
        st.warning("Please enter a question.")
    else:
        # Show loading animation while waiting for Groq response
        with st.spinner("Generating SQL..."):
            try:
                # Call Groq API — returns a dictionary with sql_query, explanation, etc.
                result = generate_sql(schema, question)

                st.subheader("Results")

                # ── SQL QUERY ──
                # st.code() shows SQL with syntax highlighting + copy button
                st.markdown("**SQL Query**")
                st.code(result.get("sql_query", "-- no query generated"), language="sql")

                # ── EXPLANATION ──
                # st.info() shows text in a blue info box
                st.markdown("**Explanation**")
                st.info(result.get("explanation", "—"))

                # ── TABLES USED & CONDITIONS — side by side ──
                col_left, col_right = st.columns(2)

                with col_left:
                    st.markdown("**🗄️ Tables Used**")
                    tables = result.get("tables_used", [])
                    # Loop through each table and display in green box
                    if tables:
                        for table in tables:
                            st.success(f"{table}")
                    else:
                        st.write("None")

                with col_right:
                    st.markdown("**Conditions Applied**")
                    conditions = result.get("conditions_applied", [])
                    if conditions:
                        for condition in conditions:
                            # UNCLEAR conditions → red error box
                            # Normal conditions → green success box
                            if condition.upper().startswith("UNCLEAR"):
                                st.error(f"{condition}")
                            else:
                                st.success(f"{condition}")
                    else:
                        st.write("None")

            # ── ERROR HANDLING ──
            except json.JSONDecodeError:
                # Model returned something that wasn't valid JSON
                st.error("Could not parse the response. Try again.")
            except Exception as e:
                # Catches everything else — wrong API key, network issue, rate limit
                st.error(f"Error: {str(e)}")