import modal

# Create Modal app
app = modal.App("interview-app")

# Create image with necessary dependencies
image = (modal.Image.debian_slim()
         .pip_install("transformers==4.36.2", "torch", "accelerate==0.26.1")
         .run_commands("apt-get update", "apt-get install -y git"))

# Questions list
QUESTIONS = [
    "What can I help you ship?",
    "Anything else you'd like to add?"
]

@app.function(
    image=image,
    gpu="A100",
    memory=32000,
    timeout=120
)
def generate_response(conversation_history):
    """Generate a follow-up question based on conversation history."""
    try:
        # Import dependencies inside the function where they'll be used
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.1"
        
        # Initialize model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Create the prompt
        prompt = """<s>[INST] You are interviewing someone about their project. Based on their responses, ask ONE specific follow-up question about:
1. Technical requirements
2. Timeline
3. Potential challenges

If you have enough information about all these aspects, respond with: 'INTERVIEW_COMPLETE: [Brief summary]'

Current conversation:
"""
        for entry in conversation_history:
            prompt += f"\nQuestion: {entry['question']}\nAnswer: {entry['response']}\n"
        prompt += "\nAsk your next question or conclude the interview.[/INST]"
        
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_new_tokens=150,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("[/INST]")[-1].strip()
        
        # Clean up
        del model
        del tokenizer
        torch.cuda.empty_cache()
        
        return response
        
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        return "I apologize, but I encountered an error. Could you please provide more details about your project?" 