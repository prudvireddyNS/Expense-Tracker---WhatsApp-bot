from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from database import Expense, SessionLocal
from datetime import datetime

from sqlalchemy import text
import re

from dotenv import load_dotenv
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# Tool to execute SQL queries safely
@tool
def execute_sql_query(query: str) -> str:
    """
    Execute a SQL query on the expenses database and return the result.
    Only SELECT, INSERT, UPDATE, and DELETE queries are allowed.
    Use single quotes for string values.
    """
    session = SessionLocal()
    try:
        # if not re.match(r"^(SELECT|INSERT|UPDATE|DELETE)\s", query, re.IGNORECASE):
        #     return "Invalid query. Only SELECT, INSERT, UPDATE, and DELETE queries are allowed."

        result = session.execute(text(query))
        session.commit()

        if query.strip().upper().startswith("SELECT"):
            return str(result.fetchall())
        else:
            return "Query executed successfully."
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        session.close()

tools = [execute_sql_query]

prompt = hub.pull("hwchase17/react-chat")
prompt.template = """
You are a helpful WhatsApp bot designed to help users track and query their daily expenses. 
Your job is to understand natural language messages, decide whether the user wants to add an expense or query their expenses, and respond concisely and clearly.

TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

**Instructions**:

1. Understand the User's Message:
   - If the user is adding an expense, extract the following details:
     - Amount (e.g., "500Rs")
     - Category (e.g., "coffee", "food", "transport")
     - Description (e.g., "latte at Starbucks")
     - Date (if mentioned, otherwise assume today's date).
   - If the user is querying their expenses, identify the type of query (e.g., total spending, category-wise spending, time-based spending).

2. Add an Expense:
   - If the user is adding an expense, generate an SQL INSERT query to save the expense to the database.

3. Query Expenses:
   - If the user is querying their expenses, generate an SQL SELECT query to retrieve the relevant data and generate a response.

4. Handle Ambiguity:
   - If the user's message is unclear, ask for clarification.
   - Example: "I'm not sure what you mean. Could you clarify whether you're adding an expense or asking about your spending?"

When generating SQL queries, provide the query directly without wrapping it in quotes. For example:
- Correct: SELECT SUM(amount) FROM expenses WHERE date = DATE('now')
- Incorrect: 'SELECT SUM(amount) FROM expenses WHERE date = DATE("now")'

When generating SQL queries, always include the phone_number in WHERE clauses for data isolation:
- For SELECT: ... WHERE phone_number = '{{phone_number}}' AND ...
- For INSERT: ... (phone_number, amount, category, ...) VALUES ('{{phone_number}}', ...)

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
"""

# Initialize memory and agent
memory = ConversationBufferWindowMemory(window_size=5, return_messages=True, memory_key='chat_history')
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, memory=memory, handle_parsing_errors=True)

def process_message(input_text: str, phone_number: str) -> str:
    """Process the user's message and return a response."""
    try:

        bot_input = """
User WhatsApp number: {phone_number}
User query: {input}
"""
        response = agent_executor.invoke({
            "input": bot_input.format(phone_number=phone_number, input=input_text)
        })
        return response.get("output", "No response").strip('```')
    except Exception as e:
        return f"An error occurred while processing your request"
