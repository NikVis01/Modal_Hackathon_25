import modal

# Create image with FastAPI installed
image = modal.Image.debian_slim().pip_install("fastapi")

app = modal.App("interview-app")

QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(image=image)
@modal.web_endpoint()
def interview(action: str = "start", question_index: int = None, user_response: str = None):
    if action == "start":
        return {
            "question": QUESTIONS[0],
            "question_index": 0
        }
    
    elif action == "chat" and question_index is not None:
        next_index = question_index + 1
        if next_index < len(QUESTIONS):
            return {
                "question": QUESTIONS[next_index],
                "question_index": next_index
            }
        else:
            return {
                "message": "Interview complete!",
                "complete": True
            }
    
    return {"error": "Invalid parameters"}

if __name__ == "__main__":
    modal.serve(app) 