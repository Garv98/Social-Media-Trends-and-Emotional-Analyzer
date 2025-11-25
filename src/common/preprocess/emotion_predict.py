import requests
import json
import logging

API_URL = "https://a3ysspj2mgd7ckhcd5tpfltomu0tmskk.lambda-url.ap-south-1.on.aws/"

def predict_emotion(text):
    try:
        response = requests.post(API_URL, json={"text": text}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Emotion prediction failed: {e}")
        return {"error": str(e)}

def enrich_with_emotion(event):
    if "text" in event:
        event["emotion_prediction"] = predict_emotion(event["text"])
    return event