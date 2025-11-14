from confluent_kafka import Consumer
import json
import sys

def run_ml_consumer(bootstrap_servers='localhost:9092', topic='social_events'):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'ml-model-team',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 5000
    })
    
    consumer.subscribe([topic])
    print(f"ML Consumer started: {bootstrap_servers} -> {topic}\n")
    
    event_count = 0
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}", file=sys.stderr)
                continue
            
            event = json.loads(msg.value().decode('utf-8'))
            event_count += 1
            
            print(f"\nEvent #{event_count}")
            print(f"  Platform: {event['platform']}")
            print(f"  Text: {event['text'][:100]}...")
            print(f"  Subreddit: {event.get('meta', {}).get('subreddit', 'N/A')}")
            print(f"  Score: {event.get('engagement', {}).get('score', 'N/A')}")
                
    except KeyboardInterrupt:
        print(f"\n\nTotal events: {event_count}")
    finally:
        consumer.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ML Model Real-Time Consumer')
    parser.add_argument('--bootstrap', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='social_events', help='Kafka topic')
    
    args = parser.parse_args()
    
    run_ml_consumer(bootstrap_servers=args.bootstrap, topic=args.topic)
