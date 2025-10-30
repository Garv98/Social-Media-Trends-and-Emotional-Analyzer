"""Test Twitter API integration"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_collector.twitter_client import TwitterAPIClient

def test_twitter_api_connection():
    """Test Twitter API connection and basic functionality"""
    print("🔑 Testing Twitter API Connection")
    print("=" * 50)
    
    api_client = TwitterAPIClient()
    
    if api_client.client:
        print("✅ Twitter API client initialized successfully")
        print(f"   Bearer token configured: {'Yes' if api_client.bearer_token else 'No'}")
        
        # Test basic API call
        try:
            print("\n📡 Testing API connection...")
            limits = api_client.get_api_limits()
            if limits:
                print("✅ API connection successful")
                print("   Rate limits retrieved successfully")
            else:
                print("⚠️  API connection test inconclusive")
        except Exception as e:
            print(f"❌ API connection test failed: {str(e)}")
        
        # Test tweet search
        print(f"\n🔍 Testing tweet search...")
        try:
            tweets = api_client.search_hashtag_tweets("#AI", max_tweets=3)
            
            if tweets:
                print(f"✅ Successfully collected {len(tweets)} tweets")
                print(f"   Sample tweet ID: {tweets[0]['id']}")
                print(f"   Sample text: {tweets[0]['text'][:60]}...")
                print(f"   Source: {tweets[0].get('source', 'unknown')}")
            else:
                print("⚠️  No tweets found (may be due to rate limits or no recent tweets)")
        except Exception as e:
            print(f"❌ Tweet search failed: {str(e)}")
    
    else:
        print("❌ Twitter API client not available")
        print("   Please check your TWITTER_BEARER_TOKEN in .env file")
    
    print(f"\n🔄 Testing Twitter API Client...")
    
    # Test API client again with different hashtag
    if api_client.client:
        try:
            tweets = api_client.search_hashtag_tweets("#Python", max_tweets=2)
            
            if tweets:
                print(f"✅ Twitter API client collected {len(tweets)} tweets")
                print(f"   Data source: {tweets[0].get('source', 'unknown')}")
            else:
                print("⚠️  Twitter API client returned no tweets")
        
        except Exception as e:
            print(f"❌ Twitter API client test failed: {str(e)}")
    
    print(f"\n🎯 Test Summary:")
    print(f"   API Available: {'Yes' if api_client.client else 'No'}")
    
    if not api_client.client:
        print(f"\n❌ No data collection methods available!")
        print(f"   1. Add TWITTER_BEARER_TOKEN to .env file for API access")
    else:
        print(f"\n✅ Data collection ready!")


def show_env_instructions():
    """Show instructions for setting up environment"""
    print(f"\n📝 Environment Setup Instructions:")
    print(f"=" * 50)
    print(f"1. Get your Twitter API Bearer Token from: https://developer.twitter.com")
    print(f"2. Add it to your .env file:")
    print(f"   TWITTER_BEARER_TOKEN=your_actual_bearer_token_here")
    print(f"3. Test the connection by running this script again")
    print(f"\n💡 Your .env file should look like:")
    print(f"   TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAABcdefgh...")
    print(f"   TARGET_HASHTAGS=#AI,#MachineLearning,#DataScience")


if __name__ == "__main__":
    test_twitter_api_connection()
    show_env_instructions()
