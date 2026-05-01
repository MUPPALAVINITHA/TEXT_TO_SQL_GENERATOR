# 🗄️ Text-to-SQL Generator

### What is this project?

A web application that converts plain English questions into SQL queries using AI. The user provides their database schema and types a question in plain English — the app generates the correct SQL query instantly.


### Problem it solves

Writing SQL requires technical knowledge. Many business users, analysts, and non-developers cannot query their own databases because they don't know SQL. This creates a bottleneck where:
- Non-technical users are dependent on developers
- Simple data questions take hours to get answered
- Mistakes happen when schema is not followed correctly

This app bridges that gap — anyone can get a SQL query by just typing a question in plain English.


### Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core programming language |
| Streamlit | Web UI framework |
| Groq API | LLM inference engine |
| LLaMA 3.1 8B | AI model that generates the SQL |
| python-dotenv | Secure API key management |


### What the app does — Step by Step

1. User pastes their **Database Schema** (table names and columns)
2. User types their **Question** in plain English
3. Clicks **Generate SQL**
4. App sends both to **Groq's LLaMA 3.1 model** with a carefully written prompt
5. Model returns a structured **JSON response**
6. App displays SQL query, explanation, tables used, and conditions applied


### Output it produces

```json
{
  "sql_query": "SELECT * FROM users WHERE age > 25",
  "explanation": "This query selects all users older than 25",
  "tables_used": ["users"],
  "conditions_applied": ["Age filter: users older than 25"]
}
```


### Key Functions

#### `build_prompt(schema, question)`
- Builds the instruction sent to the LLM
- Injects schema and question dynamically
- Includes 6 strict rules the model must follow:
  1. Use only columns from the provided schema
  2. Always list every WHERE condition in plain English
  3. Flag ambiguous terms as `UNCLEAR: <reason>`
  4. If schema is missing info → set sql_query to error message
  5. Never leave conditions_applied empty if WHERE exists
  6. Return only valid JSON

#### `generate_sql(schema, question)`
- Calls Groq API using the official Groq Python client
- Uses `llama-3.1-8b-instant` model with `temperature=0.1`
- Extracts response text from `choices[0].message.content`
- Cleans up any accidental backticks from the model
- Parses JSON string into a Python dictionary


### UI Components

| Component | Purpose |
|-----------|---------|
| `st.text_area` | Multi-line schema input |
| `st.text_input` | Single-line question input |
| `st.code` | Displays SQL with syntax highlighting + copy button |
| `st.info` | Displays explanation in blue box |
| `st.success` | Normal conditions in green box |
| `st.error` | UNCLEAR conditions in red box |


### Conditions Applied Logic

The `conditions_applied` field explains every WHERE clause in plain English:

| Condition Type | Example | Display |
|----------------|---------|---------|
| Normal condition | `Age filter: users older than 25` | 🟢 Green box |
| Unclear term | `UNCLEAR: 'recent' has no defined time range` | 🔴 Red box |
| No conditions | Query has no WHERE clause | Plain `None` text |


### Test Cases

| Case | Schema | Question | Expected Output |
|------|--------|----------|-----------------|
| Clear Request | `Table users(id, name, age, city)` | Show all users older than 25 | `SELECT * FROM users WHERE age > 25` |
| Missing Schema | `Table orders(id, amount, status)` | Show all users from New York | `-- Cannot generate: missing schema details` |
| Ambiguous Query | `Table users(id, name, age, city, created_at)` | Show recent users | `UNCLEAR: 'recent' is not defined` |

### Error Handling

| Error | Cause | Handled by |
|-------|-------|------------|
| `JSONDecodeError` | Model returned invalid JSON | Shows "Could not parse response" |
| `Exception` | Wrong API key, network issue, rate limit | Shows the error message |


<img width="800" height="500" alt="Screenshot 2026-05-01 163622" src="https://github.com/user-attachments/assets/08f4f7ae-fa2c-4d7b-9494-4ffcf4fe385d" />


<img width="800" height="500" alt="Screenshot 2026-05-01 163643" src="https://github.com/user-attachments/assets/4c3b3726-2375-44d7-b43c-1a1602b9e241" />
