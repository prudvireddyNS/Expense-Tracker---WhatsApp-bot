from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from llm import process_message
import matplotlib.pyplot as plt
import pandas as pd
from database import SessionLocal, Expense
from dotenv import load_dotenv
import os
from warnings import filterwarnings

filterwarnings("ignore")
load_dotenv()

if not os.path.exists("temp"):
    os.makedirs("temp")
app = FastAPI()
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

def get_expense_data(phone_number: str) -> pd.DataFrame:
    """
    Fetch expense data for a given phone number from the database.
    Returns a DataFrame with columns: amount, category.
    """
    session = SessionLocal()
    try:
        expenses = session.query(Expense).filter(Expense.phone_number == phone_number).all()
        if not expenses:
            return pd.DataFrame()
        data = [{"amount": e.amount, "category": e.category} for e in expenses]
        return pd.DataFrame(data)
    finally:
        session.close()

def generate_spending_chart(df: pd.DataFrame, phone_number: str) -> str:
    """
    Generate a spending summary pie chart and save it as an image.
    Returns the file path of the saved chart.
    """
    if df.empty:
        raise ValueError("No data available to generate the chart.")

    plt.clf()

    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')

    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99FFCC']

    wedges, texts, autotexts = ax.pie(
        df['amount'], 
        labels=df['category'],
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )

    plt.setp(autotexts, size=8, weight="bold")
    plt.setp(texts, size=8)

    ax.set_title('Your Spending Summary', pad=20, size=12, weight="bold")

    chart_path = f"temp/{phone_number}_summary.png"
    plt.savefig(chart_path, bbox_inches='tight', dpi=300)
    plt.close('all')

    return chart_path

@app.post("/whatsapp")
async def whatsapp_bot(request: Request, Body: str = Form(...)):
    """
    Handle incoming WhatsApp messages and respond with appropriate actions.
    """
    try:
        incoming_msg = Body.strip()
        form_data = await request.form()
        phone_number = form_data.get("From", "").replace("whatsapp:", "").strip()

        if not phone_number:
            return Response(
                content=str(MessagingResponse().message("Error: Phone number not found in request.")),
                media_type="application/xml"
            )

        response = MessagingResponse()
        message = response.message()

        if "summary" in incoming_msg.lower():
            df = get_expense_data(phone_number)
            if not df.empty:
                chart_path = generate_spending_chart(df, phone_number)
                message.media(chart_path)
                bot_response = "Here's your spending summary chart! 📊"
            else:
                bot_response = "No expenses found. Ready to track your first expense! 🚀"
        else:
            bot_response = process_message(incoming_msg, phone_number)

        message.body(bot_response)
        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        return Response(
            content=str(MessagingResponse().message(f"An error occurred: {str(e)}")),
            media_type="application/xml"
        )