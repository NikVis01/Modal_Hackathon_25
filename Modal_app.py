import modal
from fastapi import FastAPI
from pydantic import BaseModel
import json
from transformers import pipeline

image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "transformers==4.40.0",
    "torch==2.2.1",
    "sentencepiece"
)

web_app = FastAPI()

class InterviewResponse(BaseModel):
    question: str
    answer: str

QUESTIONS = [
    "Hi! What's your name?",
    "What is your email address?",
    "What is your company name and what are you planning to ship?",
    "Specify a timeframe for your project"
]

app = modal.App("interview-bot")

@app.function()
@modal.web_endpoint(method="POST")
async def chat(question_index: int, user_response: str = None):
    responses = {}

    if question_index == 0 and user_response is None:
        return {"question": QUESTIONS[0], "question_index": 0}
    
    if user_response:
        responses[QUESTIONS[question_index]] = user_response
    
    next_index = question_index + 1
    if next_index < len(QUESTIONS):
        return {
            "question": QUESTIONS[next_index],
            "question_index": next_index
        }
    else:
        return {
            "message": "Interview complete!",
            "responses": responses
        }


