#!/usr/bin/env python3
"""Fetch wrestler profile facts (height, weight, nationality, finisher) from
public, automation-friendly sources and cache them in data/wrestler_profiles.json.

Sources (both official MediaWiki/Wikibase APIs):
  * Pro Wrestling Wiki (prowrestling.fandom.com): height, weight, finishing moves
  * Wikidata: country of citizenship (German labels), height/weight fallback

The cache is read at build time by src/helpers/cswDesign.js. Manual corrections
go into data/wrestler_profile_overrides.json, keyed by wrestler slug:
  {"edge": {"wiki": "Edge (wrestler)", "wikidata": "Q44176", "finisher": "Spear"}}
Value keys (height, weight, nationality, finisher) win over fetched data;
"wiki"/"wikidata" pin the page or entity used for lookup; "skip": true disables
lookups (e.g. for fictional CSW originals).
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

USER_AGENT = "CSW-Site-Profile-Sync/1.0 (https://github.com/CptSpaulding1980/choke-slam-wrestling)"
WIKI_API = "https://prowrestling.fandom.com/api.php"
WIKI_PAGE = "https://prowrestling.fandom.com/wiki/"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_PAGE = "https://www.wikidata.org/wiki/"
REFRESH_DAYS = 180
RETRY_MISSING_DAYS = 30
PAUSE = 0.6


def fetch_json(url, params):
    query = urllib.parse.urlencode({**params, "format": "json"})
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                time.sleep(PAUSE)
                return json.load(response)
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^(title|permalink):\s*(.+)$", line)
        if match:
            value = match.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape")
            data[match.group(1)] = value.strip("'")
    return data


def roster(repo):
    wrestlers = {}
    for note in sorted((repo / "src/site/notes/Wrestler").glob("*.md")):
        meta = frontmatter(note.read_text(encoding="utf-8"))
        slug = meta.get("permalink", "").strip("/").split("/")[-1]
        if slug:
            wrestlers[slug] = meta.get("title") or note.stem
    return wrestlers


# ---------------------------------------------------------------- wiki markup
def strip_markup(text):
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"\{\{\s*(?:nowrap|small|nobr)\s*\|([^{}|]*)\}\}", r"\1", text, flags=re.I)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", text).strip(" ,;")


def infobox(wikitext):
    start = re.search(r"\{\{\s*Infobox[ _]Wrestler", wikitext, re.I)
    if not start:
        return None
    depth, i = 0, start.start()
    while i < len(wikitext):
        if wikitext.startswith("{{", i):
            depth += 1; i += 2; continue
        if wikitext.startswith("}}", i):
            depth -= 1; i += 2
            if depth == 0:
                break
            continue
        i += 1
    body = wikitext[start.end():i - 2]
    fields = {}
    for match in re.finditer(r"^\s*\|\s*([\w ]+?)\s*=\s*(.*?)(?=^\s*\||\Z)", body, re.M | re.S):
        fields[match.group(1).strip().lower()] = match.group(2).strip()
    return fields


def metric(value, unit):
    """'6 ft 1 in (1.85 m)' -> '1,85 m (6 ft 1 in)'; keep plain text otherwise."""
    value = strip_markup(value)
    if not value:
        return ""
    value = value.split(" / ")[0].split(";")[0].strip()
    if unit == "m":
        found = re.search(r"(\d+(?:[.,]\d+)?)\s*m\b", value)
        imperial = re.search(r"\d+\s*ft(?:\s*\d+\s*in)?", value)
        if found:
            meters = float(found.group(1).replace(",", "."))
            text = f"{meters:.2f}".replace(".", ",") + " m"
            return f"{text} ({imperial.group(0)})" if imperial else text
        cm = re.search(r"(\d{3})\s*cm", value)
        if cm:
            return f"{int(cm.group(1)) / 100:.2f}".replace(".", ",") + " m"
        if imperial:
            feet, _, inches = imperial.group(0).partition("ft")
            total = int(feet) * 30.48 + int(re.sub(r"\D", "", inches) or 0) * 2.54
            return f"{total / 100:.2f}".replace(".", ",") + f" m ({imperial.group(0)})"
    else:
        kg = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", value)
        lbs = re.search(r"(\d+(?:[.,]\d+)?)\s*lbs?\b", value)
        if kg:
            text = f"{round(float(kg.group(1).replace(',', '.')))} kg"
            return f"{text} ({lbs.group(1)} lbs)" if lbs else text
        if lbs:
            pounds = float(lbs.group(1).replace(",", "."))
            return f"{round(pounds * 0.4536)} kg ({lbs.group(1)} lbs)"
    return ""


def finishers(wikitext, name="", limit=2):
    match = re.search(r"^\*\s*'''\s*Finish(?:ing moves?|ers?)\s*'''(.*?)(?=^\*\s*'''|^==|\Z)", wikitext, re.S | re.M | re.I)
    if not match:
        return ""
    entries = []
    for line in match.group(1).splitlines():
        bullet = re.match(r"^([*:]+)\s*(.*)$", line.strip())
        if bullet and bullet.group(1).count("*") >= 2 or (bullet and bullet.group(1).startswith(":")):
            entries.append((len(bullet.group(1)), bullet.group(2).strip()))
    if not entries:
        return ""
    top = min(depth for depth, _ in entries)
    groups, current = [], None
    for depth, item in entries:
        label = strip_markup(item)
        if depth == top and re.match(r"^As\b", label):
            current = {"label": label, "items": []}
            groups.append(current)
        elif current is not None and depth > top:
            current["items"].append(item)
        elif depth == top:
            current = None
            groups.append({"label": "", "items": [item]})
    named = [g for g in groups if g["label"] and name and name.lower() in g["label"].lower()]
    gimmicks = [g for g in groups if g["label"]]
    chosen = named[:1] or (gimmicks[:1] if gimmicks and len(gimmicks) == len(groups) else [g for g in groups if not g["label"]])
    items = [item for group in chosen for item in group["items"]]
    moves = []
    for item in items:
        current = re.search(r"present|current", item, re.I) is not None
        move = strip_markup(item)
        while re.search(r"\([^()]*\)", move):
            move = re.sub(r"\s*\([^()]*\)", "", move)
        move = move.split("(")[0]
        move = re.split(r"\s+(?:–|-)\s+|,\s+(?:sometimes|often|usually|while|from)\b|\s+\d{4}\b", move)[0].strip(" .")
        if move and len(move) <= 60:
            moves.append((not current, len(moves), move))
    picked = [move for _, _, move in sorted(moves)][:limit]
    return ", ".join(dict.fromkeys(picked))


def wiki_profile(name, pinned=None):
    candidates = [pinned] if pinned else [name, f"{name} (wrestler)"]
    for title in candidates:
        data = fetch_json(WIKI_API, {"action": "parse", "page": title, "prop": "wikitext", "redirects": 1})
        if "parse" not in data:
            continue
        text = data["parse"]["wikitext"]["*"]
        box = infobox(text)
        if box is None:
            continue
        page = data["parse"]["title"]
        return {
            "height": metric(box.get("height", ""), "m"),
            "weight": metric(box.get("weight", ""), "kg"),
            "finisher": finishers(text, name),
            "birth_place": strip_markup(box.get("birth_place", "")),
            "url": WIKI_PAGE + urllib.parse.quote(page.replace(" ", "_")),
        }
    return None


# ------------------------------------------------------------------- wikidata
_country_labels = {}


def _names(entity):
    names = {entity.get("labels", {}).get(lang, {}).get("value", "").lower() for lang in ("en", "de")}
    for lang in ("en", "de"):
        names |= {alias["value"].lower() for alias in entity.get("aliases", {}).get(lang, [])}
    return names - {""}


def wikidata_entity(name, pinned=None, wiki_title=None):
    if pinned:
        entity = fetch_json(WIKIDATA_API, {"action": "wbgetentities", "ids": pinned, "props": "claims"})["entities"][pinned]
        return pinned, entity.get("claims", {})
    wanted = {name.lower()} | ({wiki_title.lower()} if wiki_title else set())
    # Restrict the search to people whose occupation is professional wrestler.
    for term in dict.fromkeys(filter(None, [wiki_title, name])):
        hits = fetch_json(WIKIDATA_API, {"action": "query", "list": "search", "srlimit": 5,
                                         "srsearch": f"{term} haswbstatement:P106=Q13474373"}).get("query", {}).get("search", [])
        ids = [hit["title"] for hit in hits]
        if not ids:
            continue
        entities = fetch_json(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(ids), "props": "labels|aliases|claims", "languages": "en|de"})["entities"]
        for qid in ids:
            if _names(entities[qid]) & wanted:
                return qid, entities[qid].get("claims", {})
    return None


def claim_values(claims, prop):
    values = []
    for claim in claims.get(prop, []):
        if claim.get("rank") == "deprecated":
            continue
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if value is not None:
            values.append(value)
    return values


def country_names(qids):
    missing = [q for q in qids if q not in _country_labels]
    if missing:
        entities = fetch_json(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(missing), "props": "labels", "languages": "de|en"})["entities"]
        for qid, entity in entities.items():
            labels = entity.get("labels", {})
            _country_labels[qid] = (labels.get("de") or labels.get("en") or {}).get("value", "")
    return [_country_labels[q] for q in qids if _country_labels.get(q)]


def quantity(values, kind):
    units = {"m": {"Q11573": 100, "Q174728": 1, "Q218593": 2.54, "Q3710": 30.48},
             "kg": {"Q11570": 1, "Q100995": 0.4536}}[kind]
    for value in values:
        factor = units.get(value.get("unit", "").rsplit("/", 1)[-1])
        if factor:
            amount = float(value["amount"]) * factor
            return f"{amount / 100:.2f}".replace(".", ",") + " m" if kind == "m" else f"{round(amount)} kg"
    return ""


def wikidata_profile(name, pinned=None, wiki_title=None):
    found = wikidata_entity(name, pinned, wiki_title)
    if not found:
        return None
    qid, claims = found
    countries = country_names([v["id"] for v in claim_values(claims, "P27") if isinstance(v, dict) and "id" in v])
    return {
        "nationality": " / ".join(dict.fromkeys(countries)),
        "height": quantity(claim_values(claims, "P2048"), "m"),
        "weight": quantity(claim_values(claims, "P2067"), "kg"),
        "url": WIKIDATA_PAGE + qid,
    }


# ----------------------------------------------------------------------- main
def build_profile(name, override):
    wiki = wiki_profile(name, override.get("wiki"))
    wiki_title = urllib.parse.unquote(wiki["url"].rsplit("/", 1)[-1]).replace("_", " ") if wiki else None
    wikidata = wikidata_profile(name, override.get("wikidata"), wiki_title)
    profile = {"name": name, "fetched": dt.date.today().isoformat(), "sources": {}}
    for key in ("height", "weight", "finisher", "nationality"):
        profile[key] = (wiki or {}).get(key) or (wikidata or {}).get(key) or ""
    if wiki:
        profile["sources"]["Pro Wrestling Wiki"] = wiki["url"]
    if wikidata:
        profile["sources"]["Wikidata"] = wikidata["url"]
    profile["found"] = bool(wiki or wikidata)
    return profile


def due(entry, today):
    if not entry:
        return True
    age = (today - dt.date.fromisoformat(entry.get("fetched", "2000-01-01"))).days
    return age >= (REFRESH_DAYS if entry.get("found") else RETRY_MISSING_DAYS)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--limit", type=int, default=40, help="max. wrestlers to (re)fetch per run; 0 = all due")
    parser.add_argument("--only", nargs="*", help="refresh only these wrestler names or slugs")
    parser.add_argument("--workers", type=int, default=1, help="parallel lookups (keep small to stay polite)")
    args = parser.parse_args()

    repo = args.repo.resolve()
    cache_path = repo / "data/wrestler_profiles.json"
    overrides_path = repo / "data/wrestler_profile_overrides.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
    today = dt.date.today()

    wrestlers = roster(repo)
    if args.only:
        wanted = {w.lower() for w in args.only}
        queue = [(s, n) for s, n in wrestlers.items() if s in wanted or n.lower() in wanted]
    else:
        queue = [(s, n) for s, n in wrestlers.items() if due(cache.get(s), today) and not overrides.get(s, {}).get("skip")]
        queue.sort(key=lambda item: (item[0] in cache, cache.get(item[0], {}).get("fetched", "")))
        if args.limit:
            queue = queue[:args.limit]

    updated = failed = 0

    def work(item):
        slug, name = item
        return slug, name, build_profile(name, overrides.get(slug, {}))

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(work, item) for item in queue]
        for future, (slug, name) in zip(futures, queue):
            try:
                _, _, profile = future.result()
                cache[slug] = profile
                updated += 1
                print(f"  {name}: {'ok' if profile['found'] else 'nicht gefunden'}", flush=True)
            except Exception as error:  # network trouble must not break the site build
                failed += 1
                print(f"  {name}: Fehler ({error})", file=sys.stderr, flush=True)
            if updated and updated % 20 == 0:
                cache_path.write_text(json.dumps(dict(sorted(cache.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(dict(sorted(cache.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    found = sum(1 for entry in cache.values() if entry.get("found"))
    print(f"Profile: {updated} aktualisiert, {failed} Fehler, {found}/{len(wrestlers)} mit Webdaten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
