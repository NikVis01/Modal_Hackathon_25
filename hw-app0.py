import modal
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Create a Modal app
app = modal.App("hello-world-app")

# Create a Modal image with our dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi==0.109.2",
)

# Create the FastAPI app
web_app = FastAPI()

@web_app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Hello World</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f0f2f5;
                }
                h1 {
                    color: #1a73e8;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1>Hello World!</h1>
        </body>
    </html>
    """

# Mount the FastAPI app using Modal's ASGI integration
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app 
