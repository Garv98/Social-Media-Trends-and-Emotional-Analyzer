from src.common.preprocess.emotion_predict import enrich_with_emotion
import time
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import yaml
from dotenv import load_dotenv

try:
    import praw
except Exception as e:  # pragma: no cover
    praw = None

from src.common.sinks import FileSink, KafkaSink, SupabaseSink
from src.common.preprocess.text_clean import clean_text
from src.common.preprocess.dedup import Deduplicator
from src.common.utils.metrics import MetricsLogger


def load_config(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def make_sink(cfg: Dict):
    sink_type = cfg['stream']['sink']
    if sink_type == 'file':
        c = cfg['sinks']['file']
        return FileSink(root_dir=c['root_dir'], filename_pattern=c['filename_pattern'], partition_by=c.get('partition_by', 'date'))
    elif sink_type == 'kafka':
        c = cfg['sinks']['kafka']
        return KafkaSink(bootstrap_servers=c['bootstrap_servers'], topic=c['topic'], acks=c.get('acks', 1))
    elif sink_type == 'supabase':
        c = cfg['sinks'].get('supabase', {})
        return SupabaseSink(table_name=c.get('table_name', 'reddit_posts'))
    else:
        raise ValueError(f"Unknown sink type: {sink_type}")


def init_reddit(cfg: Dict):
    if praw is None:
        raise ImportError("praw not installed. Install praw to use reddit connector.")
    return praw.Reddit(
        client_id=cfg.get('REDDIT_CLIENT_ID'),
        client_secret=cfg.get('REDDIT_CLIENT_SECRET'),
        user_agent=cfg.get('REDDIT_USER_AGENT', 'mlops-reddit-collector')
    )


def poll_once(reddit, subreddits: List[str], limit: int, query: str):
    results = []
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        if query:
            for submission in subreddit.search(query, limit=limit):
                results.append(submission)
        else:
            for submission in subreddit.new(limit=limit):
                results.append(submission)
    return results


def run_poll(config_path: str = 'configs/config.yaml'):
    load_dotenv()
    cfg = load_config(config_path)
    if not cfg['sources']['reddit']['enabled']:
        print("Reddit source disabled in config.")
        return
    sink = make_sink(cfg)
    opts = cfg['preprocess']['text']
    reddit_env = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
        'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT', 'mlops-reddit-collector')
    }
    reddit = init_reddit(reddit_env)

    subreddits = cfg['sources']['reddit']['subreddits']
    query = cfg['sources']['reddit']['query']
    poll_interval = cfg['sources']['reddit']['poll_interval_sec']
    limit_per_call = cfg['sources']['reddit']['limit_per_call']

    dedup = Deduplicator()
    metrics = MetricsLogger()
    
    try:
        while True:
            submissions = poll_once(reddit, subreddits, limit_per_call, query)
            for s in submissions:
                ts = datetime.fromtimestamp(s.created_utc, tz=timezone.utc).isoformat()
                cleaned = clean_text(s.title + " " + (s.selftext or ""), opts)
                event = {
                    'id': s.id,  # Use Reddit submission ID for dedup
                    'text': cleaned,
                    'raw_text': s.title,
                    'timestamp': ts,
                    'platform': 'reddit',
                    'engagement': {
                        'score': getattr(s, 'score', None),
                        'num_comments': getattr(s, 'num_comments', None),
                    },
                    'lang': 'en',  # reddit doesn't provide language; could integrate langdetect later
                    'meta': {
                        'subreddit': s.subreddit.display_name,
                        'query': query,
                        'submission_id': s.id
                    }
                }
                
                # Check dedup
                if dedup.is_duplicate(event):
                    metrics.log_event(deduplicated=True)
                    continue
                
                event = enrich_with_emotion(event)
                
                sink.write(event)
                metrics.log_event(deduplicated=False)
            
            # Log summary after each poll batch
            metrics.log_summary()
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        pass
    finally:
        sink.flush()
        metrics.log_summary()
        print(f"[DEDUP] {dedup.stats()}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/config.yaml')
    args = parser.parse_args()
    run_poll(config_path=args.config)
