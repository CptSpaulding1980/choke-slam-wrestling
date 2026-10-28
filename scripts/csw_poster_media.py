"""Explicit, local-only poster attachment. No generation, upload or git effects.

Callers must resolve event/part identity and approve each URL in a manifest.
This deliberately does not use the cron generator's broad Release-img removal.
"""
import re


def attach_posters(content, urls):
    """Set the primary poster and add absent body images after venue metadata.

    Existing images (including distinct part artwork), video markup, identities
    and match tables remain intact. An empty selection is never implicit removal.
    """
    if not urls:
        raise ValueError('At least one explicitly approved poster URL is required')
    sections = re.split(r'^---[ \t]*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(sections) != 3 or sections[0].strip():
        raise ValueError('Expected YAML frontmatter')
    fm, body = sections[1:]
    # Legacy notes may place an entire media flex block above the event title.
    # Move the contiguous identity block only; never regex-delete Release images.
    identity = re.search(r'^(?:# )?(?:<img[^\n]*?>)?\*\*S\d{2}E\d{2,3}[^\n]*\n(?:\s*\n)*\*\*Date:\*\*[^\n]*\n(?:\s*\n)*\*\*Venue:\*\*[^\n]*(?:\n|$)', body, re.MULTILINE)
    if identity and body[:identity.start()].strip():
        body = '\n\n' + identity.group(0) + '\n' + body[:identity.start()].lstrip('\n') + body[identity.end():]
    venue = re.search(r'^\*\*Venue:\*\*[^\n]*(?:\n|$)', body, re.MULTILINE)
    if not venue or '## Matches' not in body:
        raise ValueError('Expected venue metadata and match section')
    replacement = 'image: "' + urls[0] + '"'
    if re.search(r'^image:.*$', fm, re.MULTILINE):
        fm = re.sub(r'^image:.*$', lambda _: replacement, fm, count=1, flags=re.MULTILINE)
    else:
        fm = fm.rstrip() + '\n' + replacement + '\n'
    # Reposition only explicitly selected image tags that trail a video. Keep
    # each exact tag, all other artwork, and every byte from Matches onward.
    prefix, matches = body.split('## Matches', 1)
    video = re.search(r'<video\b', prefix)
    if video:
        trailing = [m for m in re.finditer(r'<img\b[^>]*>', prefix) if m.start() > video.start() and any(re.search(r'\bsrc=[\"\']' + re.escape(url) + r'[\"\']', m.group()) for url in urls)]
        tags = [m.group() for m in trailing]
        for match in reversed(trailing):
            prefix = prefix[:match.start()] + prefix[match.end():]
        if tags:
            prefix = prefix[:venue.end()] + '\n' + '\n'.join(tags) + '\n' + prefix[venue.end():]
            body = prefix + '## Matches' + matches
    missing = [url for url in dict.fromkeys(urls) if not re.search(r'<img\b[^>]*\bsrc=[\"\']' + re.escape(url) + r'[\"\']', body)]
    if missing:
        images = '\n'.join('<img src="' + url + '" width="300" style="border-radius:8px;">' for url in missing)
        body = body[:venue.end()] + '\n' + images + '\n' + body[venue.end():]
    return '---' + fm + '---' + body
