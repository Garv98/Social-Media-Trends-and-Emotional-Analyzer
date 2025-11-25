import sys
import json
import time
from pathlib import Path
from confluent_kafka import Producer

def delivery_report(err, msg):
    if err:
        print(f"ERROR: Delivery failed: {err}", file=sys.stderr)
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

def tail_file(file_path, producer, topic):
    """Stream new lines from file to Kafka"""
    with open(file_path, 'r', encoding='utf-8') as f:
        # Move to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    producer.produce(
                        topic,
                        key=event.get('id', '').encode('utf-8'),
                        value=line.strip().encode('utf-8'),
                        callback=delivery_report
                    )
                    producer.poll(0)
                except Exception as e:
                    print(f"ERROR: Failed to send: {e}", file=sys.stderr)
            else:
                time.sleep(1)
                producer.poll(0)

if __name__ == '__main__':
    bootstrap_servers = sys.argv[1]
    topic = sys.argv[2]
    
    config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'reddit-collector-producer'
    }
    
    producer = Producer(config)
    print(f"Kafka producer connected to {bootstrap_servers}")
    print(f"Streaming to topic: {topic}")
    
    # Get today's events file
    from datetime import datetime
    today = datetime.now()
    file_path = Path(f"data/raw/{today.year}/{today.month:02d}/{today.day:02d}/events-{today.year}-{today.month:02d}-{today.day:02d}.jsonl")
    
    if not file_path.exists():
        print(f"Waiting for file: {file_path}")
        while not file_path.exists():
            time.sleep(5)
    
    print(f"Tailing file: {file_path}")
    tail_file(file_path, producer, topic)
