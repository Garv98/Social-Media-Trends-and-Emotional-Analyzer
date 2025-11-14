import json
import sys
from typing import Optional

try:
    from confluent_kafka import Consumer
except Exception:
    Consumer = None


def run_consumer(bootstrap_servers: str, topic: str, group_id: str = "demo-consumer", out_file: Optional[str] = None):
    if Consumer is None:
        raise ImportError("confluent-kafka not installed.")
    c = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'latest'
    })
    c.subscribe([topic])
    fh = open(out_file, 'a', encoding='utf-8') if out_file else None
    try:
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}", file=sys.stderr)
                continue
            val = msg.value().decode('utf-8')
            if fh:
                fh.write(val + "\n")
                fh.flush()
            else:
                print(val)
    except KeyboardInterrupt:
        pass
    finally:
        if fh:
            fh.close()
        c.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bootstrap', default='localhost:9092')
    parser.add_argument('--topic', default='social_events')
    parser.add_argument('--group', default='demo-consumer')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    run_consumer(bootstrap_servers=args.bootstrap, topic=args.topic, group_id=args.group, out_file=args.out)
