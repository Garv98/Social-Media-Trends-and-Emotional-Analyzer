import os
import json
import logging
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMOTION_API_URL = "https://a3ysspj2mgd7ckhcd5tpfltomu0tmskk.lambda-url.ap-south-1.on.aws/"

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def predict_emotion(text):
    """Fetch emotion prediction from AWS Lambda API."""
    try:
        response = requests.post(EMOTION_API_URL, json={"text": text}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Emotion prediction failed for text: {text[:50]}... Error: {e}")
        return None

def process_and_upload(file_path):
    """Read JSONL, get predictions, and upload to Supabase."""
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    logging.info(f"Processing {len(lines)} records from {file_path}")
    
    success_count = 0
    error_count = 0
    
    # Process in batches for better efficiency (individual inserts for now for simplicity and error tracking)
    for line in tqdm(lines, desc="Uploading to Supabase"):
        try:
            post = json.loads(line)
            
            # Check if prediction exists, if not, get it
            if "emotion_prediction" not in post or not post["emotion_prediction"] or "label" not in post["emotion_prediction"]:
                prediction = predict_emotion(post["text"])
                if prediction:
                    post["emotion_prediction"] = prediction
                else:
                    logging.warning(f"Skipping post {post.get('id')} due to prediction failure.")
                    error_count += 1
                    continue

            # Format data for Supabase
            data = {
                "post_id": post["id"],
                "text": post["text"],
                "subreddit": post.get("meta", {}).get("subreddit", "unknown"),
                "emotion_label": post["emotion_prediction"]["label"],
                "emotion_score": post["emotion_prediction"]["score"],
                "engagement_score": post.get("engagement", {}).get("score", 0),
                "num_comments": post.get("engagement", {}).get("num_comments", 0),
                "raw_data": post
            }

            # Upsert into Supabase (handles duplicates if post_id is same)
            supabase.table("reddit_posts").upsert(data, on_conflict="post_id").execute()
            success_count += 1
            
        except Exception as e:
            logging.error(f"Failed to process line: {e}")
            error_count += 1

    logging.info(f"Migration completed! Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    DATA_FILE = r"d:\5th Sem\reddit garv\Social-Media-Trends-and-Emotional-Analyzer\data\raw\2025\11\25\events-2025-11-25.jsonl"
    process_and_upload(DATA_FILE)
