import requests

API_URL = "https://router.huggingface.co/hf-inference/models/deepset/roberta-base-squad2"
headers = {"Authorization": "Bearer <auth_token>"}
# Replace <auth_token> with your actual Hugging Face API token

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
	"question": "What is my name?",
	"context": "My name is Clara and I live in Berkeley."
})

print(output)