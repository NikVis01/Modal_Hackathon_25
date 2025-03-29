from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline


# a) Get predictions

# Load pre-trained model and tokenizer
model_name = "deepset/roberta-base-squad2"
nlp = pipeline('question-answering', model=model_name, tokenizer=model_name)

# Static context for the conversation
context = """
    Hello, I am Marcelon. I come from Perú, and I am selling the best guamedos in the world. 
    I sell the guamedo at the price of 1 dollar each. 
    You can find me at the Plaza de Armas in Lima, Perú, from 12.00 to 18:00.
    Shipping is available for 5 dollars.
    I accept payments only through revolut (my revolut tag is @marcelon/1234).
    Thanks for your interest in my guamedos!
    I hope to see you soon.
"""

# Chat loop
print("Chat with the LLM! Type 'exit' to quit.")
while True:
    # Get user input
    question = input("You: ")

    # Exit condition
    if question.lower() == "exit":
        print("Goodbye!")
        break

    # Prepare input for Q&A
    QA_input = {
        'question': question,
        'context': context
    }

    # Get the model's answer
    res = nlp(QA_input)

    # Print the model's answer
    print("LLM: ", res['answer'])


# b) Load model & tokenizer
model = AutoModelForQuestionAnswering.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)