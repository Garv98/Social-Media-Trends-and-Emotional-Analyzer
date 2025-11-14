import re
from typing import Dict

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@[A-Za-z0-9_]+")
HASHTAG_PATTERN = re.compile(r"#[\w_]+")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str, opts: Dict) -> str:
    if not text:
        return text
    if opts.get("lowercase", True):
        text = text.lower()
    if opts.get("remove_urls", True):
        text = URL_PATTERN.sub("", text)
    if opts.get("remove_mentions", True):
        text = MENTION_PATTERN.sub("", text)
    if opts.get("remove_hashtags", False):
        text = HASHTAG_PATTERN.sub("", text)
    if opts.get("normalize_whitespace", True):
        text = WHITESPACE_PATTERN.sub(" ", text).strip()
    return text
