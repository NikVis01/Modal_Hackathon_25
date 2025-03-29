import modal
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

# Model configuration
MODEL_ID = "gpt2"
SYSTEM_PROMPT = """You are a helpful assistant gathering shipping information. After the main questions, you need to collect:
1. The user's full name
2. Their complete mailing address

Be conversational but focused. If information is incomplete, ask for the missing details politely.
Keep your responses short and direct.

Current conversation:
"""

# Create Modal image with required packages
image = modal.Image.debian_slim().pip_install(["torch", "transformers"])

@modal.function(image=image, gpu="any", timeout=60)
def generate_response(conversation_history):
    """Generate next response using GPT-2"""
    # Initialize model and tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(MODEL_ID)
    model = GPT2LMHeadModel.from_pretrained(MODEL_ID).to("cuda")
    
    # Format conversation history
    formatted_prompt = SYSTEM_PROMPT + "\n".join(conversation_history) + "\nAssistant:"
    
    # Generate response
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id,
        repetition_penalty=1.2
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the assistant's response
    response = response.split("Assistant:")[-1].strip()
    
    return response

# Questions for the interview
QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
] 