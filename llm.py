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

from warnings import filterwarnings
filterwarnings("ignore")

llm = ChatOpenAI(model="gpt-4o-mini") 

@tool
def execute_sql_query(query: str, params: dict = None) -> str:
    """
    Execute a SQL query on the expenses database and return the result.
    Only SELECT, INSERT, UPDATE, and DELETE queries are allowed.
    Use single quotes for string values.
    """
    session = SessionLocal()
    try:
        if not re.match(r"^(SELECT|INSERT|UPDATE|DELETE)\s", query, re.IGNORECASE):
            return "Invalid query. Only SELECT, INSERT, UPDATE, and DELETE queries are allowed."

        result = session.execute(text(query), params) if params else session.execute(text(query))
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
You are ExpenseBot, a precise WhatsApp expense tracker. Your responses are brief and action-oriented, also interactive using stickers and emojis.

CORE FUNCTIONS:
1. ADD EXPENSE
   Input format: [Amount] for [Description] in [Category]
   Example: "500Rs for lunch at cafe in food"
   Action: Create INSERT query with:
   - Amount (required)
   - Category (required)
   - Description (optional)
   - Date (default: today)

2. QUERY EXPENSES
   Supported queries:
   - "total expenses" 
   - "show [category] expenses"
   - "expenses for [timeframe]"
   - "spending summary"

TOOLS:
------

Bot has access to the following tools:

{tools}

To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action


When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]


SQL RULES:
1. Use direct queries without quotes
2. Always include phone_number filter:
   SELECT: WHERE phone_number = '{{phone_number}}' AND ...
   INSERT: VALUES ('{{phone_number}}', ...)

Remember to:
1. Validate all amounts
2. Confirm actions with users
3. Show relevant emojis
4. Provide brief, clear responses

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
"""

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
        return f"An error occurred while processing your request."     