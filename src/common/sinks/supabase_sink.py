import os
from typing import Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

class SupabaseSink:
    def __init__(self, table_name: str = "reddit_posts"):
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
            
        self.client: Client = create_client(url, key)
        self.table_name = table_name

    def write(self, event: Dict[str, Any]):
        try:
            # Check if prediction exists
            if "emotion_prediction" not in event:
                logging.warning(f"Post {event.get('id')} has no emotion prediction, skipping Supabase write.")
                return

            data = {
                "post_id": event["id"],
                "text": event["text"],
                "subreddit": event.get("meta", {}).get("subreddit", "unknown"),
                "emotion_label": event["emotion_prediction"]["label"],
                "emotion_score": event["emotion_prediction"]["score"],
                "engagement_score": event.get("engagement", {}).get("score", 0),
                "num_comments": event.get("engagement", {}).get("num_comments", 0),
                "raw_data": event
            }
            
            # Upsert into Supabase
            self.client.table(self.table_name).upsert(data, on_conflict="post_id").execute()
        except Exception as e:
            logging.error(f"Failed to write to Supabase sink: {e}")

    def flush(self):
        pass
