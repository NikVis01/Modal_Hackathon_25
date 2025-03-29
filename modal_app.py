import modal

# Define the Modal application
app = modal.App("example-app")

# Create a lightweight Debian-based image with FastAPI installed
image = modal.Image.debian_slim().pip_install("fastapi[standard]")

# Define a function to compute the square of a number
@app.function()
def compute_square(x: int) -> int:
    print("Executing remotely...")
    return x ** 2

# Entry point for local execution
@app.local_entrypoint()
def main():
    result = compute_square.remote(42)
    print(f"The square is: {result}")

# Define a FastAPI endpoint using the specified image
@app.function(image=image)
@modal.fastapi_endpoint()
def hello_world():
    return "Hello, world!"
