import requests

API_URL = "https://router.huggingface.co/hf-inference/models/deepset/roberta-base-squad2"
headers = {"Authorization": "Bearer hf_XXXXX"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
	"question": "What is my name?",
	"context": "My name is Clara and I live in Berkeley."
})

print(output)