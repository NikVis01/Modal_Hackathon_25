import modal
from fastapi import FastAPI
from pydantic import BaseModel
import json
from datetime import datetime
from transformers import pipeline

volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)

image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]",
    "transformers==4.40.0",
    "torch==2.2.1",
    "sentencepiece"
)

app = modal.App("interview-app")

QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(image=image)
def init_sentiment():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@app.function(image=image)
@modal.web_endpoint()
async def interview(action: str = "start", question_index: int = None, user_response: str = None):
    """
    Single endpoint handling all interview actions:
    - /interview?action=start -> Starts interview
    - /interview?action=chat&question_index=0&user_response=John -> Handles responses
    """
    if action == "start":
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None and user_response is not None:
        responses = {}
        sentiment_analyzer = init_sentiment()
        
        sentiment = sentiment_analyzer(user_response)[0]
        
        responses[QUESTIONS[question_index]] = {
            "response": user_response,
            "sentiment": sentiment
        }
        
        next_index = question_index + 1
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
    
    return {"error": "Invalid action or missing parameters"}

if __name__ == "__main__":
    modal.serve(app) 