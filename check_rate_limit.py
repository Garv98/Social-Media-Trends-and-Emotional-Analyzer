#!/usr/bin/env python3
"""Quick Twitter API Rate Limit Checker"""
import tweepy
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def check_rate_limit():
    """Check current rate limit status"""
    print("🔍 Checking Twitter API Rate Limit Status...")
    
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("❌ No bearer token found")
        return
    
    try:
        client = tweepy.Client(bearer_token=bearer_token)
        
        response = client.search_recent_tweets(query="test", max_results=10)
        print("✅ Twitter API is ready! Rate limit has reset.")
        print(f"📊 Found {len(response.data) if response.data else 0} test tweets")
        return True
        
    except tweepy.TooManyRequests as e:
        print("⏳ Rate limit still active")
        print(f"   Error: {str(e)}")
        
        # Try to get rate limit info
        try:
            rate_limit_status = client.get_rate_limit_status()
            print("📊 Rate limit details:", rate_limit_status)
        except:
            print("   Typical wait time: 15 minutes from last request")
        
        return False
        
    except Exception as e:
        print(f"❌ Other error: {str(e)}")
        return False

if __name__ == "__main__":
    check_rate_limit()
