from confluent_kafka import Consumer
import json
import time
from collections import Counter, deque
from datetime import datetime

def clear_screen():
    print("\033[2J\033[H", end='')

def run_dashboard_consumer(bootstrap_servers='localhost:9092', topic='social_events', refresh_sec=2):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'dashboard-team',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    })
    
    consumer.subscribe([topic])
    
    total_events = 0
    platform_counts = Counter()
    subreddit_counts = Counter()
    recent_events = deque(maxlen=10)
    start_time = time.time()
    last_refresh = time.time()
    
    print(f"Dashboard starting: {bootstrap_servers} -> {topic}\n")
    time.sleep(1)
    
    try:
        while True:
            # Poll for new messages
            msg = consumer.poll(0.1)
            
            if msg is not None and not msg.error():
                event = json.loads(msg.value().decode('utf-8'))
                
                total_events += 1
                platform_counts[event['platform']] += 1
                
                # Track subreddit for reddit posts
                if event['platform'] == 'reddit':
                    subreddit = event.get('meta', {}).get('subreddit', 'unknown')
                    subreddit_counts[subreddit] += 1
                
                recent_events.append({
                    'time': event['timestamp'][:19],
                    'platform': event['platform'],
                    'text': event['text'][:60]
                })
            
            # Update dashboard display
            if time.time() - last_refresh >= refresh_sec:
                clear_screen()
                runtime = int(time.time() - start_time)
                rate = total_events / max(1, runtime) * 60
                
                print(f"REAL-TIME DASHBOARD | {datetime.now().strftime('%H:%M:%S')} | Runtime: {runtime}s\n")
                print(f"Total Events: {total_events:,} ({rate:.1f}/min)\n")
                
                if platform_counts:
                    print("By Platform:")
                    for platform, count in platform_counts.most_common():
                        pct = (count / total_events * 100) if total_events else 0
                        print(f"  {platform}: {count} ({pct:.1f}%)")
                    print()
                
                if subreddit_counts:
                    print("Top Subreddits:")
                    for subreddit, count in subreddit_counts.most_common(5):
                        print(f"  r/{subreddit}: {count}")
                    print()
                
                print("Latest Events:")
                for evt in list(recent_events)[-5:]:
                    print(f"  [{evt['time']}] {evt['platform']}: {evt['text']}...")
                
                print(f"\nPress Ctrl+C to stop")
                
                last_refresh = time.time()
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print(f"\n\nTotal: {total_events} events in {int(time.time() - start_time)}s")
    finally:
        consumer.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Dashboard Consumer')
    parser.add_argument('--bootstrap', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='social_events', help='Kafka topic')
    parser.add_argument('--refresh', type=int, default=2, help='Refresh interval in seconds')
    
    args = parser.parse_args()
    
    run_dashboard_consumer(
        bootstrap_servers=args.bootstrap,
        topic=args.topic,
        refresh_sec=args.refresh
    )
