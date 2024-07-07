from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai
import io
from PIL import Image

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the API key
API_KEY = 'AIzaSyD1PslWHfLrrWPzYJecnVm52uJWZZiJe6g'

genai.configure(api_key=API_KEY)

# Generation configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Model name
MODEL_NAME = "gemini-1.5-flash-latest"

# Create the model
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings,
    generation_config=generation_config,
)

# Function to send a message to the model
def send_message_to_model(message, image_data=None):
    chat_session = model.start_chat(history=[])
    if image_data:
        image_input = {
            'mime_type': 'image/jpeg',
            'data': image_data
        }
        response = chat_session.send_message([message, image_input])
    else:
        response = chat_session.send_message(message)
    return response.text

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

# template untuk image to ui
@app.get("/image-to-ui")
async def image_to_ui_page(request: Request):
    return templates.TemplateResponse("views/gemini.html", {"request": request})

# tempate untu chat-a
@app.get("/chat-ai")
async def chat_ai_page(request: Request):
    return templates.TemplateResponse("views/chatbot.html", {"request": request})

# template untuk flowchart
@app.get("/flow-ai")
async def flowchart_page(request: Request):
    return templates.TemplateResponse("views/diagram.html", {"request": request})

# untuk generate image
@app.post("/generate_ui")
async def generate_ui(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Generate UI description
        description_prompt = "Describe this UI in accurate details. When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. Also Describe the color of the elements."
        description = send_message_to_model(description_prompt, img_byte_arr)

        # Generate HTML
        html_prompt = f"Create an HTML file with inline CSS based on the following UI description: {description}. The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. Do not include any explanations or comments. ONLY return the HTML code with inline CSS."
        generated_html = send_message_to_model(html_prompt, img_byte_arr)

        return JSONResponse(content={"html": generated_html})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# untuk generare chat-ai
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        response = send_message_to_model(user_message)
        return JSONResponse(content={"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# untuk generate flowchart
@app.post("/flowchart")
async def flowchart(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Specific prompt to generate Mermaid.js code
        flow = f"Generate Mermaid.js diagram code for the following description: '{user_message}'. Make sure the code is enclosed in triple backticks and formatted correctly for Mermaid.js and make the diagram extend to the side instead of down, and that no Mermaid.js code is displayed"
        response = send_message_to_model(flow)
        return JSONResponse(content={"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
          
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
