import modal
import json
import os
from datetime import datetime
from infer import generate_response, QUESTIONS

# Simple image with FastAPI
image = modal.Image.debian_slim().pip_install(["fastapi"])

# Simple volume for responses
volume = modal.Volume.from_name("my-volume", create_if_missing=True)

app = modal.App("interview-app")

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint()
def interview(action: str = "start", question_index: int = None, user_response: str = None):
    data_dir = "/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    response_file = "/data/responses.json"
    
    if action == "start":
        initial_data = {
            "timestamp_started": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "responses": [],
            "conversation_history": []
        }
        with open(response_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
            
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None:
        try:
            with open(response_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "timestamp_started": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "responses": [],
                "conversation_history": []
            }
        
        data["responses"].append({
            "question": QUESTIONS[question_index] if question_index < len(QUESTIONS) else "AI Follow-up",
            "response": user_response,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        })
        
        data["conversation_history"].append(f"User: {user_response}")
        
        with open(response_file, 'w') as f:
            json.dump(data, f, indent=2)

        next_index = question_index + 1
        if next_index < len(QUESTIONS):
            return {
                "question": QUESTIONS[next_index],
                "question_index": next_index
            }
        else:
            ai_question = generate_response.remote(data["conversation_history"])
            data["conversation_history"].append(f"Assistant: {ai_question}")
            
            with open(response_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return {
                "question": ai_question,
                "question_index": next_index
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