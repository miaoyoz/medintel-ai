from fastapi import FastAPI
from api.model import *
import sys
import os
from modules.bilstm_crf import MedicalNerPredictor


app = FastAPI()

@app.post("/ai/chatbot")
def chatbot(request: Prompt):
    request_dict = request.model_dump()
    for key, value in request_dict.items():
        print(f"{key}: {value}")
    return BaseResponse(code=200, message="OK", data=request_dict)

@app.post("/ai/ner/lstm")
def ner_lstm(request: Prompt):
    print("request: ", request)
    request_dict = request.model_dump()
    response_dict = {}
    for key, value in request_dict.items():
        if key == 'content':
            predictor = MedicalNerPredictor("modules/bilstm_crf/saved_models/best_model.pth", "modules/bilstm_crf/saved_models/vocab_tags.pkl")
            entities = predictor.predict(value)
            print("识别到的实体：")
            for ent in entities:
                print(f"{ent['text']} ({ent['type']})")
                response_dict[ent['text']] = ent['type']
    return BaseResponse(code=200, message="OK", data=response_dict)