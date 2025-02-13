from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from llm import process_message
from database import SessionLocal, Expense

from dotenv import load_dotenv
load_dotenv()

from warnings import filterwarnings
filterwarnings("ignore")

app = FastAPI()

@app.post("/whatsapp")
async def whatsapp_bot(request: Request, Body: str = Form(...)):
    incoming_msg = Body.strip()
    form_data = await request.form()
    phone_number = form_data.get("From", "unknown").replace("whatsapp:", "")
    print(form_data)
    print(phone_number)

    response = MessagingResponse()
    message = response.message()

    try:
        bot_response = process_message(incoming_msg, phone_number)
        message.body(bot_response)
    except Exception as e:
        message.body(f"An error occurred while processing your request")
    return Response(content=str(response), media_type="application/xml")