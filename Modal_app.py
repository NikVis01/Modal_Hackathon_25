import modal
import json
import os
from datetime import datetime

volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)

image = modal.Image.debian_slim().pip_install("fastapi[standard]")

app = modal.App("interview-app")

QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint()
async def list_files():
    """Endpoint to check what files are in the volume"""
    if not os.path.exists("/data"):
        os.makedirs("/data")
        return {"message": "Created /data directory", "files": []}
    
    files = os.listdir("/data")
    contents = {}
    for file in files:
        if file.endswith('.json'):
            with open(f"/data/{file}", 'r') as f:
                contents[file] = json.load(f)
    
    return {
        "files": files,
        "contents": contents
    }

@app.function(image=image, volumes={"/data": volume})
@modal.web_endpoint()
async def interview(action: str = "start", question_index: int = None, user_response: str = None):
    """
    Single endpoint handling all interview actions:
    - /interview?action=start -> Starts interview
    - /interview?action=chat&question_index=0&user_response=John -> Handles responses
    """
    if not os.path.exists("/data"):
        os.makedirs("/data")
        print("Created /data directory")

    if action == "start":
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None and user_response is not None:
        responses = {}
        
        responses[QUESTIONS[question_index]] = user_response
        
        next_index = question_index + 1
        if next_index < len(QUESTIONS):
            return {
                "question": QUESTIONS[next_index],
                "question_index": next_index
            }
        else:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/data/interview_{timestamp}.json"
                with open(filename, "w") as f:
                    json.dump(responses, f)
                print(f"Saved responses to {filename}")
                
                if os.path.exists(filename):
                    print(f"Verified file exists: {filename}")
                else:
                    print(f"Warning: File not found after saving: {filename}")
                
                return {
                    "message": "Interview complete!",
                    "responses": responses,
                    "saved_to": filename
                }
            except Exception as e:
                print(f"Error saving responses: {str(e)}")
                return {
                    "error": f"Failed to save responses: {str(e)}",
                    "responses": responses
                }
    
    return {"error": "Invalid action or missing parameters"}

if __name__ == "__main__":
    modal.serve(app) 