import modal
import json
import os
from datetime import datetime

# Create image with FastAPI installed
image = modal.Image.debian_slim().pip_install("fastapi")

# Create volume for storing responses
volume = modal.Volume.from_name("Responses", create_if_missing=True)

app = modal.App("interview-app")

QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(image=image, volumes=volume)
@modal.web_endpoint()
def interview(action: str = "start", question_index: int = None, user_response: str = None):
    # Ensure data directory exists in volume
    data_dir = "/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if action == "start":
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None:
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_file = f"/data/response_{timestamp}.json"
        
        # Save the response
        response_data = {
            "timestamp": timestamp,
            "question": QUESTIONS[question_index],
            "response": user_response
        }
        
        # Write to JSON file in volume
        with open(response_file, 'w') as f:
            json.dump(response_data, f, indent=2)

        # Continue with next question or complete
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

# Add endpoint to check saved responses
@app.function(image=image, volume=volume)
@modal.web_endpoint()
def check_responses():
    data_dir = "/data"
    if not os.path.exists(data_dir):
        return {"status": "No responses yet"}
    
    files = os.listdir(data_dir)
    responses = []
    
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join(data_dir, file), 'r') as f:
                responses.append(json.load(f))
    
    return {
        "status": "success",
        "responses": responses
    }

if __name__ == "__main__":
    modal.serve(app) 