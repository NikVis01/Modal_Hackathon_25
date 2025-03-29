import modal
import json
import os
from datetime import datetime

# Create image with FastAPI installed
image = modal.Image.debian_slim().pip_install("fastapi")

# Create volume for storing responses
volume = modal.Volume.from_name("my-volume", create_if_missing=True)

app = modal.App("interview-app")

QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint()
def interview(action: str = "start", question_index: int = None, user_response: str = None):
    # Ensure data directory exists in volume
    data_dir = "/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    response_file = "/data/responses.json"
    
    if action == "start":
        # Initialize/reset the responses file when starting new interview
        initial_data = {
            "timestamp_started": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "responses": []
        }
        with open(response_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
            
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None:
        # Load existing responses
        try:
            with open(response_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "timestamp_started": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "responses": []
            }
        
        # Add new response
        data["responses"].append({
            "question": QUESTIONS[question_index],
            "response": user_response,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        })
        
        # Save updated responses
        with open(response_file, 'w') as f:
            json.dump(data, f, indent=2)

        next_index = question_index + 1
        if next_index < len(QUESTIONS):
            return {
                "question": QUESTIONS[next_index],
                "question_index": next_index
            }
        else:
            return {
                "message": "Interview complete! Responses saved.",
                "complete": True
            }
    
    return {"error": "Invalid parameters"}

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint()
def check_responses():
    response_file = "/data/responses.json"
    
    try:
        with open(response_file, 'r') as f:
            data = json.load(f)
            return {
                "status": "success",
                "data": data
            }
    except FileNotFoundError:
        return {
            "status": "No responses yet",
            "data": None
        }
    except json.JSONDecodeError:
        return {
            "status": "Error reading responses",
            "data": None
        }

if __name__ == "__main__":
    modal.serve(app) 