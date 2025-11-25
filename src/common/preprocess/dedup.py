import hashlib
import json
import os
from typing import Dict, Set


class Deduplicator:
    """Persistent deduplication tracker using IDs and content hashes."""

    def __init__(self, persist_file: str = 'data/dedup_cache.json'):
        self.persist_file = persist_file
        self.seen_ids: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        self.load_persist()

    def load_persist(self):
        """Load persisted dedup data from file."""
        if os.path.exists(self.persist_file):
            try:
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_ids = set(data.get('ids', []))
                    self.seen_hashes = set(data.get('hashes', []))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load dedup cache: {e}")

    def save_persist(self):
        """Save dedup data to file."""
        try:
            os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
            data = {
                'ids': list(self.seen_ids),
                'hashes': list(self.seen_hashes)
            }
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save dedup cache: {e}")

    def _content_hash(self, text: str) -> str:
        """Generate SHA256 hash of normalized text."""
        normalized = text.lower().strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def is_duplicate(self, event: Dict) -> bool:
        """Check if event is a duplicate by ID or content hash.
        
        Returns:
            True if duplicate, False if new.
        """
        # Check ID-based dedup
        event_id = event.get('id')
        if event_id and event_id in self.seen_ids:
            return True

        # Check content-based dedup
        text = event.get('text', '')
        if text:
            content_hash = self._content_hash(text)
            if content_hash in self.seen_hashes:
                return True

        # Not a duplicate - mark as seen and save
        if event_id:
            self.seen_ids.add(event_id)
        if text:
            self.seen_hashes.add(content_hash)
        self.save_persist()
        
        return False

    def mark_seen(self, event: Dict):
        """Explicitly mark event as seen (for post-validation)."""
        event_id = event.get('id')
        if event_id:
            self.seen_ids.add(event_id)
        text = event.get('text', '')
        if text:
            self.seen_hashes.add(self._content_hash(text))
        self.save_persist()

    def stats(self) -> Dict:
        """Return dedup statistics."""
        return {
            'unique_ids': len(self.seen_ids),
            'unique_hashes': len(self.seen_hashes)
        }
