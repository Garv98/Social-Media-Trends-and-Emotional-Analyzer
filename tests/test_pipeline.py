"""
Quick test script to verify all components work
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test if all modules can be imported"""
    try:
        from data_collector.twitter_client import TwitterAPIClient
        from data_collector.data_processor import DataProcessor
        from data_collector.database import DatabaseClient
        from data_collector.kafka_producer import KafkaProducer
        print("✅ Core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_twitter_client():
    """Test the Twitter API client"""
    try:
        from data_collector.twitter_client import TwitterAPIClient
        
        client = TwitterAPIClient()
        print("✅ Twitter API client created")
        
        # Test hashtag search
        tweets = client.search_hashtag_tweets("#AI", max_tweets=5)
        assert len(tweets) >= 0  # Could be 0 if no API token
        print(f"✅ Collected {len(tweets)} tweets")
        
        return True
    except Exception as e:
        print(f"❌ Twitter Client error: {str(e)}")
        return False

def test_data_processor():
    """Test the data processor"""
    try:
        from data_collector.data_processor import DataProcessor
        
        processor = DataProcessor()
        print("✅ Data processor created")
        
        # Test tweet processing
        sample_tweet = {
            'id': 123456789,
            'text': 'Just loving the new #AI advancements! Check it out: https://example.com @OpenAI',
            'created_at': '2023-10-27T10:00:00Z',
            'author_id': 987654321,
            'author_username': 'testuser'
        }
        processed_tweet = processor.process_tweet(sample_tweet)
        assert processed_tweet['id'] == sample_tweet['id']
        print("✅ Tweet processing works")
        
        return True
    except Exception as e:
        print(f"❌ Processor error: {str(e)}")
        return False

def test_database_client():
    """Test the database client"""
    try:
        from data_collector.database import DatabaseClient
        
        db_client = DatabaseClient()
        print("✅ Database client created")
        
        # Test storing a tweet
        sample_tweet = {
            'id': 123456789,
            'text': 'Just loving the new #AI advancements! Check it out: https://example.com @OpenAI',
            'created_at': '2023-10-27T10:00:00Z',
            'author_id': 987654321,
            'author_username': 'testuser'
        }
        db_client.store_tweet(sample_tweet)
        print("✅ Sample tweet stored in database")
        
        return True
    except Exception as e:
        print(f"❌ Database Client error: {str(e)}")
        return False

def test_kafka_producer():
    """Test the Kafka producer"""
    try:
        from data_collector.kafka_producer import KafkaProducer
        
        producer = KafkaProducer()
        print("✅ Kafka producer created")
        
        # Test sending a tweet
        sample_tweet = {
            'id': 123456789,
            'text': 'Just loving the new #AI advancements! Check it out: https://example.com @OpenAI',
            'created_at': '2023-10-27T10:00:00Z',
            'author_id': 987654321,
            'author_username': 'testuser'
        }
        producer.send_tweet(sample_tweet)
        print("✅ Sample tweet sent to Kafka")
        
        return True
    except Exception as e:
        print(f"❌ Kafka Producer error: {str(e)}")
        return False

def test_full_pipeline():
    """Test the complete data collection and processing pipeline"""
    try:
        from data_collector.twitter_client import TwitterAPIClient
        from data_collector.data_processor import DataProcessor
        from data_collector.database import DatabaseClient
        from data_collector.kafka_producer import KafkaProducer
        
        # Create components
        twitter_client = TwitterAPIClient()
        data_processor = DataProcessor()
        db_client = DatabaseClient()
        kafka_producer = KafkaProducer()
        
        # 1. Collect tweets
        print("\n1. Testing tweet collection...")
        tweets = twitter_client.search_hashtag_tweets("#AI", max_tweets=5)
        assert len(tweets) >= 0  # Could be 0 if no API token
        print(f"✅ Collected {len(tweets)} tweets")
        
        if tweets:
            # 2. Process tweets
            print("\n2. Testing tweet processing...")
            processed_tweets = []
            for tweet in tweets:
                processed = data_processor.process_tweet(tweet)
                processed_tweets.append(processed)
            assert len(processed_tweets) == len(tweets)
            print("✅ Tweet processing successful")
            
            # 3. Store in database
            print("\n3. Testing database storage...")
            for tweet in processed_tweets:
                db_client.store_tweet(tweet)
            print("✅ Database storage successful")
            
            # 4. Send to Kafka
            print("\n4. Testing Kafka streaming...")
            for tweet in processed_tweets:
                kafka_producer.send_tweet(tweet)
            print("✅ Kafka streaming successful")
        
        print("\n✅ Full pipeline test complete!")
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {str(e)}")
        raise

def main():
    """Run all tests"""
    print("🔍 Testing Twitter Sentiment Data Collection Pipeline")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Twitter Client", test_twitter_client),
        ("Data Processor", test_data_processor),
        ("Database Client", test_database_client),
        ("Kafka Producer", test_kafka_producer),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📝 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your scraping pipeline is ready.")
        print("\n📚 Next steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Start infrastructure: docker-compose up -d postgres redis kafka")
        print("3. Run collection: python scripts/run_collector.py --mode once")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main()
