# WhatsApp Expense Tracker Bot

A smart WhatsApp bot that helps users track and manage their daily expenses using natural language processing.

## Features

- Track expenses directly through WhatsApp messages
- Natural language processing for expense entry and queries
- Category-based expense tracking
- Query total spending and category-wise expenses
- Secure data isolation per user phone number

## Tech Stack

- FastAPI for backend API
- SQLite database with SQLAlchemy ORM
- GPT-4-mini for natural language processing
- Twilio for WhatsApp integration
- Langchain for LLM operations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in .env:
```bash
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_database_url
```

3. Run the server:
```bash
uvicorn app:app --reload
```
