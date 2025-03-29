import modal
from fastapi import FastAPI
from pydantic import BaseModel
import json
from datetime import datetime
from transformers import pipeline

volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)

# Setup image
image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]",
    "transformers==4.40.0",
    "torch==2.2.1",
    "sentencepiece"
)

app = modal.App("interview-app")

class ChatRequest(BaseModel):
    question_index: int
    user_response: str

QUESTIONS = [
    "Hi! What's your name?",
    "What is your email address?",
    "What is your company name and what are you planning to ship?",
    "Specify a timeframe for your project"
]

@app.function(image=image)
def init_sentiment():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@app.function(image=image)
@modal.web_endpoint()
async def root():
    return {"message": "Interview Bot API is running"}

@app.function(image=image)
@modal.web_endpoint()
async def start():
    return {
        "question": QUESTIONS[0],
        "question_index": 0
    }

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint(method="POST")  # Explicitly set POST method
async def chat(request: ChatRequest):  # Accept JSON body
    responses = {}
    sentiment_analyzer = init_sentiment()
    
    sentiment = sentiment_analyzer(request.user_response)[0]
    
    responses[QUESTIONS[request.question_index]] = {
        "response": request.user_response,
        "sentiment": sentiment
    }
    
    next_index = request.question_index + 1
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

if __name__ == "__main__":
    modal.serve(app) 