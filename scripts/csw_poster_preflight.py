"""Read-only event poster/identity checks shared by the installed CSW pipeline."""
import re
import json
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

import yaml


def has_duplicate_cards(events):
    """Fail closed on exact nonempty card repeats; never auto-alias/dedupe."""
    seen = set()
    for event in events:
        if not event['matches']:
            continue
        key = (event['title'], event['venue'], event['location'],
               json.dumps(event.get('match_identity', event['matches']), sort_keys=True, ensure_ascii=False))
        if key in seen:
            return True
        seen.add(key)
    return False


def preserved_event_prefix(content, date, title):
    """Keep curated metadata/media only for an exact official event identity."""
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) != 3 or '## Matches' not in content:
        return None
    metadata = yaml.safe_load(parts[1]) or {}
    code = re.search(r'S\d{2}E\d{2,3}', title, re.I)
    if (metadata.get('title') != title or str(metadata.get('date')) != date
            or not code or not event_poster(content, code.group())):
        return None
    return content.split('## Matches', 1)[0]


class _Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.sources.append(dict(attrs).get('src', ''))


def event_poster(content, code):
    """Recognize an explicit episode poster target, never a logo/display width."""
    parts = re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) != 3:
        return None
    metadata = yaml.safe_load(parts[1]) or {}
    images = _Images()
    images.feed(parts[2].split('## Matches', 1)[0])
    for source in [metadata.get('image', '')] + images.sources:
        if not isinstance(source, str):
            continue
        path = unquote(urlparse(source).path)
        filename = path.rsplit('/', 1)[-1]
        if ('poster' in filename.lower()
                and re.search(r'(?<![A-Za-z0-9])' + re.escape(code) + r'(?![A-Za-z0-9])', filename, re.I)
                and (path.startswith('/img/') or '/releases/download/images/' in path)):
            return source
    return None
