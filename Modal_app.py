import modal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  ## NOT IN USE BUT NEEDED LATER
from pydantic import BaseModel
import json
from datetime import datetime
from transformers import pipeline

# Create a new volume that will persist between runs
volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)

image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]",
    "transformers==4.40.0",
    "torch==2.2.1",
    "sentencepiece"
)

web_app = FastAPI()

class ChatResponse(BaseModel):
    question_index: int
    user_response: str

QUESTIONS = [
    "Hi! What's your name?",
    "What is your email address?",
    "What is your company name and what are you planning to ship?",
    "Specify a timeframe for your project"
]

app = modal.App("user-interview")

@app.function(image=image) ### SENTIMENT LAYER BULLSHIT
def init_sentiment():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@web_app.post("/start")
async def start_chat():
    return {
        "question": QUESTIONS[0],
        "question_index": 0
    }

@app.function(image=image, volumes={"/data": volume})
@web_app.post("/chat")
async def chat(response: ChatResponse):
    responses = {}
    sentiment_analyzer = init_sentiment()
    
    sentiment = sentiment_analyzer(response.user_response)[0]
    
    responses[QUESTIONS[response.question_index]] = {
        "response": response.user_response,
        "sentiment": sentiment
    }
    
    next_index = response.question_index + 1
    if next_index < len(QUESTIONS):
        return {
            "question": QUESTIONS[next_index],
            "question_index": next_index
        }
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/data/interview_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(responses, f)
        
        return {
            "message": "Interview complete!",
            "responses": responses
        }

@modal.asgi_app()
def fastapi_app():
    return web_app 