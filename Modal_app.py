import modal
import json
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create volume and set up image
volume = modal.Volume.from_name(name="interview-storage", create_if_missing=True)
image = (modal.Image.debian_slim()
         .pip_install("fastapi[standard]")
         .pip_install("openai"))

# Create FastAPI app
web_app = FastAPI()

# Add CORS middleware with more permissive settings
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Modal app
app = modal.App("interview-app")

SYSTEM_PROMPT = """You are an AI interviewer helping to gather information about a potential project. 
Your goal is to collect the following information naturally through conversation:
- Name
- Email address
- Country
- Project description (which comes from their first response)
- Timeline

Guidelines:
- Keep responses concise and friendly
- Ask for only one piece of missing information at a time
- If you detect any required information in their response, note it
- If information is unclear or incomplete, ask for clarification
- Once all information is collected, provide a summary"""

@app.function(secrets=[modal.Secret.from_name("openai-secret")])
def get_llm_response(conversation_history, collected_info):
    from openai import OpenAI
    
    client = OpenAI()
    
    # Create messages array
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history
    messages.extend(conversation_history)
    
    # Add context about what information we have/need
    context = "\nCurrently collected information:\n"
    for key, value in collected_info.items():
        context += f"- {key}: {'✓' if value else '❌'}\n"
    messages.append({"role": "system", "content": context})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
    )
    
    return response.choices[0].message.content

@web_app.get("/interview")
async def interview(action: str = "start", question_index: int = None, user_response: str = None):
    if not os.path.exists("/data"):
        os.makedirs("/data")

    # File to store conversation and collected info
    conversation_file = "/data/conversation.json"
    
    # Initialize or load conversation state
    if os.path.exists(conversation_file):
        with open(conversation_file, 'r') as f:
            state = json.load(f)
    else:
        state = {
            "conversation_history": [],
            "collected_info": {
                "project_description": None,
                "name": None,
                "email": None,
                "country": None,
                "timeline": None
            }
        }

    if action == "start":
        # Start new conversation
        state = {
            "conversation_history": [],
            "collected_info": {
                "project_description": None,
                "name": None,
                "email": None,
                "country": None,
                "timeline": None
            }
        }
        
        initial_question = "What can I help you ship?"
        state["conversation_history"].append({
            "role": "assistant",
            "content": initial_question
        })
        
        with open(conversation_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "question": initial_question,
            "question_index": 0
        }
    
    elif action == "chat" and user_response:
        # Add user response to history
        state["conversation_history"].append({
            "role": "user",
            "content": user_response
        })
        
        # For first response, save as project description
        if question_index == 0:
            state["collected_info"]["project_description"] = user_response
        
        # Get LLM response
        llm_response = get_llm_response.remote(
            state["conversation_history"],
            state["collected_info"]
        )
        
        # Add LLM response to history
        state["conversation_history"].append({
            "role": "assistant",
            "content": llm_response
        })
        
        # Save updated state
        with open(conversation_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Check if all info is collected
        if all(state["collected_info"].values()):
            return {
                "message": llm_response,
                "complete": True
            }
        
        return {
            "question": llm_response,
            "question_index": len(state["conversation_history"]) // 2
        }

    return {"error": "Invalid parameters"}

@app.function(image=image, volumes={"/data": volume})
@modal.asgi_app()
def fastapi_app():
    return web_app

if __name__ == "__main__":
    modal.serve(app) 