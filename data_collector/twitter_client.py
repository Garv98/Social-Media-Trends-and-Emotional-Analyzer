import tweepy
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
import time
import random

load_dotenv()

class TwitterAPIClient:
    """Twitter API v2 client with rate limiting and structured data access"""
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.logger = self._setup_logger()
        self._setup_client()
    
    def _setup_logger(self):
        logger = logging.getLogger('TwitterAPIClient')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def _setup_client(self):
        """Setup Twitter API client with error handling"""
        if not self.bearer_token:
            self.logger.error("No Twitter API bearer token found. Please set TWITTER_BEARER_TOKEN in .env file")
            self.client = None
            return
        
        try:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True
            )
            
            try:
                test_response = self.client.search_recent_tweets(query="test", max_results=10)
                if test_response.data or test_response.meta:
                    self.logger.info("Twitter API client initialized successfully")
                else:
                    self.logger.warning("Twitter API connection test succeeded but returned no data")
            except Exception as e:
                self.logger.warning(f"Twitter API connection test failed: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter API client: {str(e)}")
            self.client = None
    
    def search_hashtag_tweets(self, hashtag: str, max_tweets: int = 100, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Search for tweets containing specific hashtag using Twitter API
        
        Args:
            hashtag: Hashtag to search for (e.g., '#AI' or 'AI')
            max_tweets: Maximum number of tweets to collect (max 100 per request)
            days_back: Number of days to look back
            
        Returns:
            List of tweet dictionaries
        """
        if not self.client:
            self.logger.error("Twitter API client not available")
            return []
        
        tweets = []
        
        try:
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"
            
            query = f"{hashtag} -is:retweet lang:en"
            
            self.logger.info(f"Starting Twitter API search for query: {query}")
            self.logger.info(f"Target: {max_tweets} tweets (limited by API rate limits)")
            
            tweets_paginator = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations', 'lang'],
                user_fields=['username', 'verified', 'public_metrics'],
                expansions='author_id',
                max_results=min(max_tweets, 100)
            ).flatten(limit=max_tweets)
            
            for i, tweet in enumerate(tweets_paginator):
                try:
                    tweet_data = {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'author_id': tweet.author_id,
                        'author_username': None,  # Will be populated if user data available
                        'public_metrics': tweet.public_metrics or {
                            'retweet_count': 0,
                            'like_count': 0,
                            'reply_count': 0,
                            'quote_count': 0
                        },
                        'hashtags': self._extract_hashtags(tweet.text),
                        'mentions': self._extract_mentions(tweet.text),
                        'urls': self._extract_urls(tweet.text),
                        'timestamp': int(time.time()),
                        'source': 'twitter_api_v2'
                    }
                    
                    tweets.append(tweet_data)
                    
                    if (i + 1) % 25 == 0:
                        self.logger.info(f"Processed {i + 1}/{max_tweets} tweets for {hashtag}")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing tweet {i}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully collected {len(tweets)} tweets for {hashtag} via Twitter API")
            return tweets
            
        except tweepy.TooManyRequests:
            self.logger.warning("Twitter API rate limit exceeded. Please wait before making more requests.")
            return tweets  # Return what we have so far
        except tweepy.Unauthorized:
            self.logger.error("Twitter API unauthorized. Check your bearer token.")
            return []
        except Exception as e:
            self.logger.error(f"Error with Twitter API search for {hashtag}: {str(e)}")
            return []
    
    def search_multiple_hashtags(self, hashtags: List[str], tweets_per_hashtag: int = 100) -> List[Dict[str, Any]]:
        """
        Search multiple hashtags using Twitter API
        
        Args:
            hashtags: List of hashtags to search
            tweets_per_hashtag: Number of tweets per hashtag (respecting API limits)
            
        Returns:
            Combined list of all tweets
        """
        all_tweets = []
        
        for hashtag in hashtags:
            self.logger.info(f"Starting Twitter API collection for hashtag: {hashtag}")
            tweets = self.search_hashtag_tweets(hashtag, tweets_per_hashtag)
            all_tweets.extend(tweets)
            
            time.sleep(2)
        
        self.logger.info(f"Total tweets collected via Twitter API: {len(all_tweets)}")
        return all_tweets
    
    def get_user_tweets(self, username: str, max_tweets: int = 100) -> List[Dict[str, Any]]:
        """
        Get tweets from a specific user using Twitter API
        
        Args:
            username: Twitter username (without @)
            max_tweets: Maximum number of tweets to collect
            
        Returns:
            List of tweet dictionaries
        """
        if not self.client:
            self.logger.error("Twitter API client not available")
            return []
        
        tweets = []
        
        try:
            self.logger.info(f"Getting tweets from user: @{username} via Twitter API")
            
            # Get user ID first
            user = self.client.get_user(username=username)
            if not user.data:
                self.logger.error(f"User @{username} not found")
                return []
            
            user_id = user.data.id
            
            # Get user's tweets
            tweets_paginator = tweepy.Paginator(
                self.client.get_users_tweets,
                id=user_id,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                max_results=min(max_tweets, 100)
            ).flatten(limit=max_tweets)
            
            for tweet in tweets_paginator:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'author_id': user_id,
                    'author_username': username,
                    'public_metrics': tweet.public_metrics or {
                        'retweet_count': 0,
                        'like_count': 0,
                        'reply_count': 0,
                        'quote_count': 0
                    },
                    'hashtags': self._extract_hashtags(tweet.text),
                    'mentions': self._extract_mentions(tweet.text),
                    'urls': self._extract_urls(tweet.text),
                    'timestamp': int(time.time()),
                    'source': 'twitter_api_v2'
                }
                
                tweets.append(tweet_data)
            
            self.logger.info(f"Collected {len(tweets)} tweets from @{username} via Twitter API")
            return tweets
            
        except tweepy.TooManyRequests:
            self.logger.warning("Twitter API rate limit exceeded for user tweets")
            return tweets
        except Exception as e:
            self.logger.error(f"Error getting tweets from @{username}: {str(e)}")
            return []
    
    def get_api_limits(self) -> Dict[str, Any]:
        """Get current API rate limit status"""
        if not self.client:
            return {}
        
        try:
            limits = self.client.get_rate_limit_status()
            return {
                'search': limits.data.get('search', {}),
                'users': limits.data.get('users', {}),
                'tweets': limits.data.get('tweets', {})
            }
        except Exception as e:
            self.logger.error(f"Error getting API limits: {str(e)}")
            return {}
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        return re.findall(r'#\w+', text.lower())
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract user mentions from text"""
        import re
        return re.findall(r'@\w+', text.lower())
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        import re
        return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)


# Example usage and testing
if __name__ == "__main__":
    # Test the Twitter API client
    print("🐦 Testing Twitter API Client")
    print("=" * 40)
    
    # Initialize the client
    api_client = TwitterAPIClient()
    
    if api_client.client:
        print("✅ Twitter API client initialized successfully")
        
        # Test single hashtag search
        print("\n📝 Testing hashtag search...")
        tweets = api_client.search_hastag_tweets("#AI", max_tweets=5)
        
        print(f"✅ Collected {len(tweets)} tweets via Twitter API")
        if tweets:
            print("\n📄 Sample tweet:")
            tweet = tweets[0]
            print(f"   ID: {tweet['id']}")
            print(f"   Text: {tweet['text'][:80]}...")
            print(f"   Created: {tweet['created_at']}")
            print(f"   Hashtags: {tweet['hashtags']}")
            print(f"   Engagement: {tweet['public_metrics']['like_count']} likes")
        
        # Test API limits
        print(f"\n📊 Checking API rate limits...")
        limits = api_client.get_api_limits()
        if limits:
            print(f"✅ API limits retrieved successfully")
            
    print("\n🎯 Twitter API Integration Complete!")
    print("\n💡 Next steps:")
    print("   1. Add your TWITTER_BEARER_TOKEN to .env file")
    print("   2. Test with your target hashtags")
    print("   3. Monitor API rate limits")
