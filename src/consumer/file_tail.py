import json
import os
import time
from pathlib import Path
from typing import Optional


def tail_jsonl_files(root_dir: str, callback, poll_interval: float = 1.0, follow: bool = True):
    """Tail JSONL files in a directory tree, calling callback for each new event.
    
    Args:
        root_dir: Root directory to watch (e.g., data/raw)
        callback: Function to call with each event dict
        poll_interval: How often to check for new data (seconds)
        follow: If True, continuously watch for new events (like tail -f)
    """
    root = Path(root_dir)
    file_positions = {}  # Track read positions per file
    
    while True:
        # Find all JSONL files
        for filepath in root.rglob("*.jsonl"):
            filepath_str = str(filepath)
            
            # Get current file size
            if not filepath.exists():
                continue
            file_size = filepath.stat().st_size
            
            # Get last known position
            last_pos = file_positions.get(filepath_str, 0)
            
            # If file grew, read new lines
            if file_size > last_pos:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.seek(last_pos)
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                event = json.loads(line)
                                callback(event)
                            except json.JSONDecodeError as e:
                                print(f"[ERROR] Failed to parse JSON: {e}")
                    # Update position
                    file_positions[filepath_str] = f.tell()
        
        if not follow:
            break
        
        time.sleep(poll_interval)


def print_event(event: dict):
    """Simple callback that prints events."""
    print(f"[{event.get('timestamp', 'N/A')}] {event.get('platform', '?')}: {event.get('text', '')[:80]}")


def save_to_file(out_path: str):
    """Returns a callback that appends events to a file."""
    def callback(event: dict):
        with open(out_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return callback


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Tail JSONL event files")
    parser.add_argument('--root', default='data/raw', help='Root directory to watch')
    parser.add_argument('--out', default=None, help='Output file to append events (optional)')
    parser.add_argument('--poll-interval', type=float, default=1.0, help='Poll interval in seconds')
    parser.add_argument('--no-follow', action='store_true', help='Read once and exit (do not follow)')
    args = parser.parse_args()
    
    if args.out:
        callback = save_to_file(args.out)
        print(f"Tailing {args.root} -> {args.out}")
    else:
        callback = print_event
        print(f"Tailing {args.root} (press Ctrl+C to stop)")
    
    try:
        tail_jsonl_files(
            root_dir=args.root,
            callback=callback,
            poll_interval=args.poll_interval,
            follow=not args.no_follow
        )
    except KeyboardInterrupt:
        print("\nStopped.")
