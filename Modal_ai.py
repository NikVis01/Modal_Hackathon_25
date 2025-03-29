import modal
import json
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infer import app, generate_response, QUESTIONS

# Create FastAPI app
web_app = FastAPI()

# Add CORS middleware
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create volume for storing responses
volume = modal.Volume.from_name("my-volume", create_if_missing=True)

# Create web image
web_image = modal.Image.debian_slim().pip_install("fastapi", "uvicorn")

@app.function(image=web_image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_app():
    return web_app

@web_app.get("/")
async def interview(action: str = "start", question_index: int = None, user_response: str = None):
    """Handle interview interactions"""
    data_dir = "/data"
    os.makedirs(data_dir, exist_ok=True)
    response_file = "/data/responses.json"
    
    try:
        if action == "start":
            # Start new interview
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
        
        elif action == "chat" and question_index is not None and user_response:
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
            current_question = QUESTIONS[question_index] if question_index < len(QUESTIONS) else "AI Follow-up"
            data["responses"].append({
                "question": current_question,
                "response": user_response,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            })
            
            # Save responses
            with open(response_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Generate next question
            if question_index >= len(QUESTIONS) - 1:
                try:
                    next_question = generate_response.remote(data["responses"])
                    
                    if "INTERVIEW_COMPLETE" in next_question:
                        return {
                            "message": "Interview complete! Responses saved.",
                            "complete": True,
                            "summary": next_question
                        }
                    
                    return {
                        "question": next_question,
                        "question_index": len(data["responses"])
                    }
                except Exception as e:
                    print(f"Error generating response: {str(e)}")
                    return {
                        "error": "Failed to generate next question. Please try again."
                    }
            else:
                return {
                    "question": QUESTIONS[question_index + 1],
                    "question_index": question_index + 1
                }
        
        return {"error": "Invalid parameters"}
    
    except Exception as e:
        print(f"Error in interview endpoint: {str(e)}")
        return {"error": "An unexpected error occurred"}

@web_app.get("/check_responses")
async def check_responses():
    """Retrieve saved responses"""
    try:
        with open("/data/responses.json", 'r') as f:
            data = json.load(f)
            return {"status": "success", "data": data}
    except FileNotFoundError:
        return {"status": "No responses yet", "data": None}
    except json.JSONDecodeError:
        return {"status": "Error reading responses", "data": None}
    except Exception as e:
        print(f"Error checking responses: {str(e)}")
        return {"status": "error", "message": "An unexpected error occurred"}

if __name__ == "__main__":
    modal.serve(app) 