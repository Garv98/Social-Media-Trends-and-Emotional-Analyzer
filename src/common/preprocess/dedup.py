import hashlib
from typing import Dict, Set


class Deduplicator:
    """In-memory deduplication tracker using IDs and content hashes."""

    def __init__(self):
        self.seen_ids: Set[str] = set()
        self.seen_hashes: Set[str] = set()

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
            self.seen_hashes.add(content_hash)

        # Mark ID as seen
        if event_id:
            self.seen_ids.add(event_id)

        return False

    def mark_seen(self, event: Dict):
        """Explicitly mark event as seen (for post-validation)."""
        event_id = event.get('id')
        if event_id:
            self.seen_ids.add(event_id)
        text = event.get('text', '')
        if text:
            self.seen_hashes.add(self._content_hash(text))

    def stats(self) -> Dict:
        """Return dedup statistics."""
        return {
            'unique_ids': len(self.seen_ids),
            'unique_hashes': len(self.seen_hashes)
        }
