from fastapi import FastAPI
from .model import *


app = FastAPI()

@app.post("/ai/chatbot")
def chatbot(request: Prompt):
    request_dict = request.model_dump()
    for key, value in request_dict.items():
        print(f"{key}: {value}")
    return BaseResponse(code=200, message="OK", data=request_dict)