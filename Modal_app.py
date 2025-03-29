import modal
import json
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

# Create volumes and set up images
volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)
image = (modal.Image.debian_slim()
         .pip_install("fastapi[standard]")
         .pip_install("openai"))

app = modal.App("interview-app")
stub = FastAPI()

# Add CORS middleware
stub.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INITIAL_QUESTION = "What can I help you ship?"

# Required information we want to collect
REQUIRED_INFO = {
    "name": False,
    "email": False,
    "project_description": False,
    "timeline": False
}

SYSTEM_PROMPT = """You are an AI interviewer helping to gather information about a potential project. 
Your goal is to collect the following information naturally through conversation:
- Name
- Email address
- Project description
- Timeline/deadline

Guidelines:
- Keep responses concise and friendly
- Ask for only one piece of missing information at a time
- If you detect any required information in their response, note it
- If information is unclear or incomplete, ask for clarification
- Once all information is collected, provide a summary

Current conversation context and missing information will be provided."""

@app.function(secrets=[modal.Secret.from_name("openai-secret")])
def get_llm_response(conversation_history, missing_info):
    import requests

    # Define API endpoint (modify based on your Hugging Face model)
    HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

    # Load Hugging Face API Key from secrets
    HF_API_KEY = ".."
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    # Prepare messages for Mistral
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)

    # Add missing information context
    missing_fields = [k for k, v in missing_info.items() if not v]
    context = f"\nMissing information: {', '.join(missing_fields)}"
    messages.append({"role": "system", "content": context})

    # Prepare request payload
    payload = {"inputs": messages}

    # Make request to Hugging Face Inference API
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["generated_text"]
    else:
        return "Sorry, there was an issue with the AI service."

@app.function(image=image, volumes={"/data": volume})
@modal.fastapi_endpoint()
async def interview(action: str = "start", question_index: int = None, user_response: str = None):
    # Add CORS headers to the response
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    
    if not os.path.exists("/data"):
        os.makedirs("/data")

    # Initialize or load conversation state
    conversation_file = "/data/current_conversation.json"
    if os.path.exists(conversation_file):
        with open(conversation_file, 'r') as f:
            state = json.load(f)
    else:
        state = {
            "conversation_history": [],
            "required_info": REQUIRED_INFO.copy(),
            "complete": False
        }

    if action == "start":
        # Start new conversation
        state = {
            "conversation_history": [
                {"role": "assistant", "content": INITIAL_QUESTION}
            ],
            "required_info": REQUIRED_INFO.copy(),
            "complete": False
        }
        
        with open(conversation_file, 'w') as f:
            json.dump(state, f)
        
        return {"question": INITIAL_QUESTION, "question_index": 0}, headers
    
    elif action == "chat" and user_response:
        # Add user response to history
        state["conversation_history"].append({"role": "user", "content": user_response})
        
        # Get LLM response
        llm_response = get_llm_response.remote(
            state["conversation_history"],
            state["required_info"]
        )
        
        # Add LLM response to history
        state["conversation_history"].append({"role": "assistant", "content": llm_response})
        
        # Save current state
        with open(conversation_file, 'w') as f:
            json.dump(state, f)
        
        # If all information is collected, save final response
        if all(state["required_info"].values()):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_file = f"/data/interview_{timestamp}.json"
            with open(final_file, 'w') as f:
                json.dump(state, f)
            state["complete"] = True
            
            return {
                "message": "Interview complete!",
                "question": llm_response,
                "complete": True
            }, headers
        
        return {
            "question": llm_response,
            "question_index": len(state["conversation_history"]) // 2,
            "complete": False
        }, headers
    
    return {"error": "Invalid action or missing parameters"}, headers

if __name__ == "__main__":
    modal.serve(app) 