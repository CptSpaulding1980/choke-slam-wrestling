import pandas as pd
import xml.etree.ElementTree as ET
import re
import os
import sys
import subprocess
import yaml
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import base64
from datetime import datetime
from itertools import product
from openpyxl import Workbook
from openpyxl.styles import Font

# =============================================================================
# 0. KONFIGURATION & PFADE
# =============================================================================

# QUELLE (Echt) — via Env oder Default
PFAD_XML_SOURCE = os.environ.get(
    "CHOKE_SLAM_XML",
    "/Volumes/SSD_4TB/nextcloud/app/data/hendrik/files/Fire Prowrestling World/MotW_Data/SaveGames/ChokeSlam/Choke_Slam_Wrestling.xml"
)

# ASSETS
PFAD_RATING_KEY = "Star Ratings Schlüssel.xlsx" 
PFAD_EDITS_CSV = os.environ.get(
    "CHOKE_SLAM_EDITS",
    "/Volumes/SSD_4TB/nextcloud/app/data/hendrik/files/Fire Prowrestling World/MotW_Data/SaveGames/ChokeSlam/Edits.csv"
)

# OUTPUT
PFAD_EXCEL_OUTPUT = os.environ.get("CHOKE_SLAM_EXCEL", "Choke_Slam_export.xlsx")
GIT_REPO_DIR = os.environ.get("CHOKE_SLAM_REPO", os.path.expanduser("~/repos/choke-slam-wrestling"))
sys.path.insert(0, os.path.join(GIT_REPO_DIR, 'scripts'))
from csw_poster_preflight import preserved_event_prefix
NOTES_BASE_DIR = os.path.join(GIT_REPO_DIR, "src/site/notes") 
# Website First: Bilder in den globalen Image-Ordner
IMG_BASE_DIR = os.path.join(GIT_REPO_DIR, "docs/img")
CHART_DIR = os.path.join(IMG_BASE_DIR, "charts")

PATHS = {
    "events":        os.path.join(NOTES_BASE_DIR, "Events"),
    "wrestler":      os.path.join(NOTES_BASE_DIR, "Wrestler"),
    "stats":         os.path.join(NOTES_BASE_DIR, "Statistiken"),
    "championships": os.path.join(NOTES_BASE_DIR, "Championships")
}

# =============================================================================
# WRESTLER ALIASES
# =============================================================================

WRESTLER_ALIASES = {
    "Vader": "Big Van Vader",
    "Brother Nero": "Jeff Hardy",
    "Bryan Danielson": "Daniel Bryan",
    "WALTER": "Gunther",
    "Cactus Jack": "Mick Foley",
    "Mankind": "Mick Foley",
    "Dude Love": "Mick Foley",
    "Consequences Creed": "Xavier Woods",
    "Killshot": "Swerve Strickland",
    "KONOSUKE TAKESHITA": "Konosuke Takeshita",
}

CANONICAL_ALIASES = {}
for _alias, _canonical in WRESTLER_ALIASES.items():
    CANONICAL_ALIASES.setdefault(_canonical, []).append(_alias)

def get_canonical_name(name):
    """Map alias to canonical name; return name unchanged if not an alias."""
    return WRESTLER_ALIASES.get(name, name)

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def push_to_github():
    print("\n--- GIT UPLOAD START ---")
    if not os.path.exists(GIT_REPO_DIR):
        print(f"❌ Git Repo nicht gefunden: {GIT_REPO_DIR}")
        return

    # Force Git to recognize changes by touching a file
    last_run_file = os.path.join(GIT_REPO_DIR, ".last_run")
    with open(last_run_file, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    subprocess.run(["git", "add", ".last_run"], cwd=GIT_REPO_DIR, check=False)
    try:
        subprocess.run(["git", "add", "."], cwd=GIT_REPO_DIR, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=GIT_REPO_DIR, capture_output=True, text=True)
        if status.stdout.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            subprocess.run(["git", "commit", "-m", f"Auto-Update: Wrestling Ergebnisse {ts}"], cwd=GIT_REPO_DIR, check=True)
            subprocess.run(["git", "push"], cwd=GIT_REPO_DIR, check=True)
            print("✅ Erfolgreich gepusht!")
        else:
            print("ℹ️ Keine Änderungen zum Hochladen.")
    except Exception as e:
        print(f"❌ Fehler bei Git: {e}")

def load_rating_map():
    """Built-in star rating map — no external Excel file needed."""
    r_map = {}
    # 0-49 = DUD
    for i in range(0, 50):
        r_map[i] = "DUD"
    # 50-55 = ★
    for i in range(50, 56):
        r_map[i] = "★"
    # 56-59 = ★½
    for i in range(56, 60):
        r_map[i] = "★½"
    # 60-63 = ★★
    for i in range(60, 64):
        r_map[i] = "★★"
    # 64-67 = ★★½
    for i in range(64, 68):
        r_map[i] = "★★½"
    # 68-71 = ★★★
    for i in range(68, 72):
        r_map[i] = "★★★"
    # 72-75 = ★★★¼
    for i in range(72, 76):
        r_map[i] = "★★★¼"
    # 76-79 = ★★★½
    for i in range(76, 80):
        r_map[i] = "★★★½"
    # 80-83 = ★★★¾
    for i in range(80, 84):
        r_map[i] = "★★★¾"
    # 84-87 = ★★★★
    for i in range(84, 88):
        r_map[i] = "★★★★"
    # 88-91 = ★★★★¼
    for i in range(88, 92):
        r_map[i] = "★★★★¼"
    # 92-95 = ★★★★½
    for i in range(92, 96):
        r_map[i] = "★★★★½"
    # 96-99 = ★★★★¾
    for i in range(96, 100):
        r_map[i] = "★★★★¾"
    # 100-103 = ★★★★★
    for i in range(100, 104):
        r_map[i] = "★★★★★"
    # 104 = ★★★★★¼
    r_map[104] = "★★★★★¼"
    # 105 = ★★★★★½
    r_map[105] = "★★★★★½"
    # 106 = ★★★★★¾
    r_map[106] = "★★★★★¾"
    # 107 = ★★★★★★
    r_map[107] = "★★★★★★"
    return r_map

def get_star_rating(rating_num, r_map):
    try:
        rating_val = float(rating_num)
        rating = int(round(rating_val))
        if rating in r_map: return r_map[rating]
        if rating_val < 50: return "DUD"
        return f"{rating}★"
    except:
        return str(rating_num)

def slugify(t):
    return re.sub(r"[^a-z0-9\-]", "", re.sub(r"[\s_]+", "-", str(t).lower()))

# Link Enrichment
def enhanced_smart_link(text, participants):
    if pd.isna(text): return ""
    text = str(text)
    participants = str(participants)
    text = re.sub(r"\((w|W)/", "(TEMP_SECOND:", text)

    all_entities = []
    for entity in participants.split(","):
        entity = entity.strip()
        if entity:
            all_entities.append(entity)
            if entity.endswith("Jr") or entity.endswith("Jr."):
                base_name = re.sub(r"\s*Jr\.?$", "", entity)
                all_entities.append(base_name)

    teams_map = {
        "Militanter Mummenschanz": "[[Teams/Militanter Mummenschanz\|Militanter Mummenschanz]]",
        "Saint Rebel Radicalz": "[[Teams/Saint Rebel Radicalz\|Saint Rebel Radicalz]]",
        "Sweet 'n Sour Elite": "[[Teams/Sweet 'n Sour Elite\|Sweet 'n Sour Elite]]",
        "Path of God": "[[Teams/Path of God\|Path of God]]",
        "Nature Gamemasters": "[[Teams/Nature Gamemasters\|Nature Gamemasters]]"
    }
    for team, link in teams_map.items():
        text = re.sub(rf"(?<!\[)\b{re.escape(team)}\b(?!\])", link, text)

    for entity in sorted(set(all_entities), key=len, reverse=True):
        if not any(x in entity for x in ["[[", "]]", "Championship"]):
            text = re.sub(rf"(?<!\[)\b{re.escape(entity)}\b(?!\])", f"[[Wrestler/{entity}\|{entity}]]", text)

    text = re.sub(r"\(TEMP_SECOND:([^)]+)\)", lambda m: f"({m.group(1)[0]}/[[Wrestler/{m.group(1)[1:].strip()}\|{m.group(1)[1:].strip()}]])", text)
    
    # Match Types Patterns
    patterns = [
        (r"\b([A-Z]{2,}[\w\s-]+(?:Championship|Title|Belt))\b", r"[[\1]]"),
        (r"(Steel Cage|Tables|Ladder|Royal Rumble|Battle Royal|Hell in a Cell|Iron Man|Empty Arena|Falls Count Anywhere|Texas Death|Last Man Standing|2 out of 3 Falls|No DQ|No Disqualification|No Count Out|No Holds Barred|Extreme Rules|I Quit|Street Fight)\b", r"[[\1]]")
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def normalize_title(matchdict_or_str):
    CHAMPIONSHIP_WHITELIST = {
        "Choke Slam World Championship": "Choke Slam World Championship",
        "Choke Slam International Championship": "Choke Slam International Championship",
        "Choke Slam Womens Championship": "Choke Slam Womens Championship",
        "Choke Slam Tag Team Championship": "Choke Slam Tag Team Championship",
        "Choke Slam Trios Championship": "Choke Slam Trios Championship",
        "Choke Slam World Trios Championship": "Choke Slam Trios Championship",
    }
    if isinstance(matchdict_or_str, str): matchdict = {"name": matchdict_or_str}
    else: matchdict = matchdict_or_str or {}

    champ_col = str(matchdict.get("Championship", "")).strip()
    if champ_col:
        for key, mapped in CHAMPIONSHIP_WHITELIST.items():
            if key.casefold() in champ_col.casefold(): return mapped

    title = str(matchdict.get("name") or matchdict.get("Match") or matchdict.get("match") or "").strip()
    if not title: return None

    # Simple whitelist check in title
    for key, mapped in CHAMPIONSHIP_WHITELIST.items():
        if key.casefold() in title.casefold(): return mapped
    return None

def format_champion_link(winner_str):
    """
    Format a winner string (comma-separated wrestlers) into Obsidian links.
    "Gunther, The Undertaker" → "[[Wrestler/Gunther|Gunther]] & [[Wrestler/The Undertaker|The Undertaker]]"
    "Steve Austin" → "[[Wrestler/Steve Austin|Steve Austin]]"
    "Vacant" → "Vacant"
    "nan" → "??"
    """
    if pd.isna(winner_str) or not str(winner_str).strip():
        return "??"
    wrestlers = [x.strip() for x in str(winner_str).split(",") if x.strip()]
    if not wrestlers:
        return "??"
    if len(wrestlers) == 1:
        name = wrestlers[0]
        if name.lower() == "vacant":
            return "Vacant"
        return f"[[Wrestler/{name}\\|{name}]]"
    # Team/Trios: link each member individually
    links = []
    for name in wrestlers:
        if name.lower() == "vacant":
            links.append("Vacant")
        else:
            links.append(f"[[Wrestler/{name}\\|{name}]]")
    return " & ".join(links)

# =============================================================================
# TEIL 1: XML ZU EXCEL
# =============================================================================
def part1_xml_to_excel():
    print("1. Starte XML Verarbeitung...")
    if not os.path.exists(PFAD_XML_SOURCE):
        print(f"❌ XML Datei nicht gefunden: {PFAD_XML_SOURCE}")
        return False

    r_map = load_rating_map()

    def get_star_text(rating_raw):
        try:
            r_fl = float(rating_raw)
            r_rd = int(round(r_fl))
            return r_map.get(r_rd, f"{r_rd}★")
        except: return "?"

    def extract_time_from_finish(finish):
        match = re.search(r"(\d{1,2})\s*Min\s*(\d{1,2})\s*Sec", finish)
        if match: return f"{int(match.group(1))}:{int(match.group(2)):02d}"
        return "0:00"

    def extract_stipulation(match_name):
        stip_keywords = ["Submission", "Last Man Standing", "No Holds Barred", "Street Fight", "Steel Cage", "Tornado", "Elimination Chamber", "Money in the Bank", "Royal Rumble", "Battle Royal", "Triple Threat", "Tag Team", "2 out of 3 Falls", "Beat the Clock", "Three Way", "No Disqualification", "No Count Out", "SWA Rules", "Extreme Rules", "Exploding Landmine Death", "Tables", "Beat the Clock", "Ladder", "Hell in a Cell", "Special Referee", "Threeway", "Hardcore", "Empty Arena", "Texas Death", "Battle Royale", "Iron Man"]
        extracted = []
        for kw in stip_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", match_name, re.IGNORECASE): extracted.append(kw)
        return ", ".join(sorted(set(extracted)))

    with open(PFAD_XML_SOURCE, "r", encoding="utf-8") as file:
        full_content = file.read()

    start_tag, end_tag = "<Cards>", "</Cards>"
    start_index = full_content.find(start_tag)
    end_index = full_content.find(end_tag) + len(end_tag)
    if start_index == -1: return False
    
    # Fix unescaped ampersands in XML content (game generates invalid XML)
    xml_content = full_content[start_index:end_index]
    xml_content = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', xml_content)
    root = ET.fromstring(xml_content)
    matches = []

    for card in root.findall(".//Card"):
        # Fail closed: only explicitly Finished cards are published. Missing or
        # unknown statuses never imply completion, even with partial results.
        status = card.findtext("Status")
        if status != "Finished":
            print(f"⏭️ Card ausgeschlossen: {card.findtext('Name') or 'Unbenannte Show'} "
                  f"(Status={status or '<missing>'})")
            continue
        show = (card.findtext("Name") or "Unbenannte Show").replace("#", "")
        date = card.findtext("Date") or "Unbekanntes Datum"
        location_text = card.findtext("Location") or ""
        venue, location_city = "", ""
        if " - " in location_text:
            parts = location_text.split(" - ", 1)
            venue, location_city = parts[0].strip(), parts[1].strip()
        else: venue = location_text.strip()
            
        for match in card.findall(".//Match"):
            match_name = match.findtext("Name") or ""
            finish = match.findtext("FinishString") or ""
            time_min = int(match.findtext("TimeMin") or 0)
            time_sec = int(match.findtext("TimeSec") or 0)
            rating_num = int(match.findtext("Rating") or 0)
            notes = match.findtext("Notes") or ""
            title_name = match.findtext("TitleName") or ""
            
            championship, is_championship = ("", False) if title_name.strip().lower() in ["none", ""] else (title_name.strip(), True)
            duration = f"{time_min}:{time_sec:02d}" if (time_min or time_sec) else extract_time_from_finish(finish)
            
            finish_lower = finish.lower()
            draw_keywords = ["draw", "no contest", "time limit", "double ko", "no winner", "stoppage"]
            is_draw = any(k in finish_lower for k in draw_keywords)

            slot_map = {}
            for w in match.findall(".//WrestlerInfo"):
                slot = w.findtext("Slot")
                name = w.findtext("Name")
                second = w.findtext("Second")
                if slot and name and name.lower() != "none" and str(second).lower() != "true":
                    slot_map[int(slot)] = get_canonical_name(name.strip())
            
            participants = ", ".join(slot_map.values())
            winner_slots = [int(x.text) for x in match.findall(".//Winners/int") if x.text]
            loser_slots = [int(x.text) for x in match.findall(".//Losers/int") if x.text]
            winners = [slot_map[s] for s in winner_slots if s in slot_map]
            losers = [slot_map[s] for s in loser_slots if s in slot_map]

            if (match.findtext("RoyalRumble") or "").strip().lower() == "true":
                # Extra entrants are added outside MotW: saved slots are not the
                # Rumble result/roster. Only explicit result names are reliable.
                winner_text = (match.findtext("WinnerString") or "").strip()
                loser_text = (match.findtext("LoserString") or "").strip()
                winners = [get_canonical_name(winner_text)] if winner_text else []
                losers = [] if re.fullmatch(r"\d+\s+other\s+wrestlers?", loser_text, re.I) else [
                    get_canonical_name(n.strip())
                    for n in re.split(r",\s*(?:&\s*)?|\s*&\s*", loser_text)
                    if n.strip() and n.strip().lower() != "none"
                ]
                participants = ", ".join(dict.fromkeys(winners + losers))
                if not winner_text:
                    print(f"⚠️ Rumble ohne WinnerString: {show} / {match_name}")

            matches.append({
                "Show": show, "Datum": date, "Venue": venue, "Location": location_city,
                "Match": match_name, "Stipulation": extract_stipulation(match_name),
                "Championship": championship, "Teilnehmer": participants,
                "Winner": ", ".join(winners) if not is_draw else "",
                "Loser": ", ".join(losers) if not is_draw else "",
                "Draw": ", ".join(slot_map.values()) if is_draw else "",
                "Finish": finish.strip(". "), "Dauer": duration,
                "Bewertung (Numerisch)": rating_num,
                "Bewertung (Sterne)": get_star_text(rating_num),
                "Anmerkungen": notes, "IsChampionship": is_championship
            })

    df = pd.DataFrame(matches)
    # Mapping
    championship_name_map = {
        "Choke Slam World Champion": "Choke Slam World Championship",
        "Choke Slam Tag Team Champion": "Choke Slam Tag Team Championship",
        "Choke Slam Womens Champion": "Choke Slam Womens Championship",
        "Choke Slam International Champion": "Choke Slam International Championship",
        "Choke Slam Trios Champions": "Choke Slam Trios Championship",
    }
    df["Championship"] = df["Championship"].map(championship_name_map).fillna(df["Championship"])

    os.makedirs(os.path.dirname(PFAD_EXCEL_OUTPUT) if os.path.dirname(PFAD_EXCEL_OUTPUT) else '.', exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "Matches"
    ws.append(df.columns.tolist())
    for row in df.itertuples(index=False): ws.append(list(row))
    wb.save(PFAD_EXCEL_OUTPUT)
    print(f"✅ Export abgeschlossen: {PFAD_EXCEL_OUTPUT}")
    # Also copy to Nextcloud for sharing
    NC_PATH = "/Volumes/SSD_4TB/nextcloud/app/data/hendrik/files/Fire Prowrestling World/Choke_Slam_export.xlsx"
    try:
        import shutil
        shutil.copy2(PFAD_EXCEL_OUTPUT, NC_PATH)
        print(f"📤 Kopie in Nextcloud: {NC_PATH}")
    except Exception as e:
        print(f"⚠️ Nextcloud-Kopie fehlgeschlagen: {e}")
    return True

# =============================================================================
# TEIL 2: EVENTS & INDEX
# =============================================================================
def part2_events():
    print("2. Generiere Events...")
    if not os.path.exists(PFAD_EXCEL_OUTPUT): return
    df = pd.read_excel(PFAD_EXCEL_OUTPUT); df.columns = [c.strip() for c in df.columns]
    r_map = load_rating_map()
    os.makedirs(PATHS['events'], exist_ok=True)
    stip_col = "Stipulation" if "Stipulation" in df.columns else None

    # Events Generieren
    df['Datum'] = pd.to_datetime(df['Datum'])
    
    # Filter for posters: Removed lookup logic to force check for all events
    # unique_events = df.drop_duplicates(subset=['Datum', 'Show']).sort_values('Datum', ascending=False)
    # poster_candidates = ... (REMOVED)
    # poster_lookup = {}
    
    # for _, row in poster_candidates.iterrows():
    #    ... (REMOVED)


    for (date_raw, show), group in df.groupby(["Datum", "Show"]):
        try: date_str = pd.to_datetime(date_raw).strftime("%Y-%m-%d")
        except: date_str = str(date_raw)
        
        filename = f"{date_str} - {show}"
        filepath = os.path.join(PATHS['events'], f"{filename}.md")
        venue = str(group["Venue"].iloc[0]).strip() if pd.notna(group["Venue"].iloc[0]) else ""
        location = str(group["Location"].iloc[0]).strip() if pd.notna(group["Location"].iloc[0]) else ""
        event_slug = slugify(f"{date_str}-{show}")
        
        # Poster: Default ChokeSlam.png (separater generate_posters.py Cron-Job updated später)
        yaml_image = "https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/ChokeSlam.png"
        poster_embed = ""  # Poster werden vom separaten Cron-Job eingefügt

        existing_prefix = None
        if os.path.exists(filepath):
            with open(filepath, encoding='utf-8') as existing:
                existing_prefix = preserved_event_prefix(existing.read(), date_str, show)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"---\ndg-publish: true\npermalink: /events/{event_slug}/\ntitle: \"{show}\"\ndate: \"{date_str}\"\npromotion: \"Choke Slam Wrestling\"\n")
            f.write(f"venue: \"{venue}\"\nlocation: \"{location}\"\n")
            f.write(f'image: "{yaml_image}"\n---\n\n')
            
            # Header — KEIN # vor HTML! (bricht Eleventy, siehe S07E12-Fix)
            f.write(f'<img src="https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/ChokeSlam.png" width="40" style="vertical-align:bottom; margin-right:8px;">**{show}**\n\n')
                
            f.write(f"**Date:** {date_str}\n")
            if venue: f.write(f"**Venue:** {venue} - {location}"+chr(10)+chr(10))
            
            # Poster (Left aligned, small)
            if poster_embed: f.write(f"{poster_embed}\n\n")
            
            f.write("## Matches\n\n| Nr. | Type | Match | Finish | Time | Rating | Score |\n|-----|------|-------|--------|------|--------|-------|\n")
            for idx, (_, row) in enumerate(group.iterrows(), 1):
                 match_link = enhanced_smart_link(row['Match'], row['Teilnehmer'])
                 stars = get_star_rating(row.get('Bewertung (Numerisch)', 0), r_map)
                 stip = str(row.get(stip_col, "")).strip() if stip_col else ""
                 if stip.lower() == "nan": stip = ""
                 f.write(f"| {idx} | {stip} | {match_link} | {row.get('Finish','')} | {row.get('Dauer','')} | {stars} | {int(row.get('Bewertung (Numerisch)', 0))} |\n")
            f.write("\n## Links\n- [[Events\|📅 Alle Events]]\n- [[Wrestler\|🤼 Roster & Stats]]\n")

        if existing_prefix is not None:
            with open(filepath, encoding='utf-8') as generated:
                results = generated.read().split('## Matches', 1)[1]
            with open(filepath, 'w', encoding='utf-8') as preserved:
                preserved.write(existing_prefix + '## Matches' + results)

    print("2.1 Generiere Events Index...")
    df['Datum'] = pd.to_datetime(df['Datum'])
    events_list = []
    for (date_val, show), group in df.groupby(['Datum', 'Show']):
        date_str = date_val.strftime("%Y-%m-%d")
        events_list.append({"date": date_val, "date_str": date_str, "show": show, "filename": f"{date_str} - {show}", "matches": len(group)})
    events_list.sort(key=lambda x: x['date'], reverse=True)
    
    with open(os.path.join(NOTES_BASE_DIR, "Events.md"), "w", encoding="utf-8") as f:
        f.write("---\ndg-publish: true\npermalink: /events/\ntitle: Events\n---\n\n# Events\n\n| Date | Event | Matches |\n|---|---|---|\n")
        for e in events_list:
            title_clean = e['show'].replace("|", "-")
            f.write(f"| {e['date_str']} | [[Events/{e['filename']}\|{title_clean}]] | {e['matches']} |\n")

# =============================================================================
# ELO & CHARTS (NO ELO VISUAL)
# =============================================================================
def calculate_elo_history(df):
    print("📈 Berechne Elo Ratings...")
    DEFAULT_ELO = 1200; K_FACTOR = 32
    elo_history = {}; current_elo = {}
    df_sorted = df.sort_values(by=['Datum']).reset_index(drop=True)
    def get_elo(w): return current_elo.get(w, DEFAULT_ELO)
    
    for _, row in df_sorted.iterrows():
        date = row['Datum']
        winners = [x.strip() for x in str(row.get('Winner','')).split(',') if x.strip()]
        losers = [x.strip() for x in str(row.get('Loser','')).split(',') if x.strip()]
        draws = [x.strip() for x in str(row.get('Draw','')).split(',') if x.strip()]
        participants = winners + losers + draws
        if not participants: continue
        
        for p in participants:
            if p not in current_elo:
                current_elo[p] = DEFAULT_ELO
                elo_history[p] = [(pd.Timestamp("2000-01-01"), DEFAULT_ELO)]
        
        if winners and losers:
            avg_w_elo = sum(get_elo(w) for w in winners) / len(winners)
            avg_l_elo = sum(get_elo(l) for l in losers) / len(losers)
            expected_w = 1 / (1 + 10 ** ((avg_l_elo - avg_w_elo) / 400))
            elo_change = K_FACTOR * (1 - expected_w)
            for w in winners:
                current_elo[w] += elo_change
                elo_history[w].append((date, current_elo[w]))
            for l in losers:
                current_elo[l] -= elo_change
                elo_history[l].append((date, current_elo[l]))
    return elo_history, current_elo

def generate_donut_chart(name, wins, losses, draws):
    total = wins + losses + draws
    if total == 0: return ""
    os.makedirs(CHART_DIR, exist_ok=True)
    filename = f"{slugify(name)}_stats.png"
    path = os.path.join(CHART_DIR, filename)
    
    # Colors for Choke Slam (Green/Red/Grey)
    colors = ['#27ae60', '#c0392b', '#95a5a6'] 
    labels = ['Wins', 'Losses', 'Draws']
    sizes = [wins, losses, draws]
    
    labels = [l for l, s in zip(labels, sizes) if s > 0]
    colors = [c for c, s in zip(colors, sizes) if s > 0]
    sizes = [s for s in sizes if s > 0]
    
    plt.figure(figsize=(3, 3)) # Kleiner
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, pctdistance=0.85, wedgeprops=dict(width=0.4))
    plt.title(f"Record: {wins}-{losses}-{draws}")
    plt.tight_layout()
    plt.savefig(path, transparent=True)
    plt.close()
    return f"<img src=\"/img/charts/{filename}\" width=\"200\">" # Kleiner im HTML

# =============================================================================
# TEIL 3: WRESTLER
# =============================================================================
def part3_wrestlers():
    print("3. Generiere Wrestler Statistiken...")
    if not os.path.exists(PFAD_EXCEL_OUTPUT): return
    df = pd.read_excel(PFAD_EXCEL_OUTPUT); df.columns = [c.strip() for c in df.columns]
    df['Datum'] = pd.to_datetime(df['Datum'])
    os.makedirs(PATHS['wrestler'], exist_ok=True)
    
    elo_history, current_elo = calculate_elo_history(df)
    edits_dict = {}
    if os.path.exists(PFAD_EDITS_CSV):
        try:
            edf = pd.read_csv(PFAD_EDITS_CSV).drop_duplicates(subset=['Name'])
            edits_dict = edf.set_index('Name')[['Height', 'Weight', 'Finisher']].to_dict('index')
        except: pass

    def clean_name(n): return re.sub(r'\s*\(.*?\)', '', n).strip()
    def parse_list(row, col): return [clean_name(x) for x in str(row.get(col, '')).split(',') if x.strip()]

    wrestlers = {}
    # Match counter for secondary sort within same date
    match_idx = 0
    # Iterate matches for stats
    for _, row in df.iterrows():
        match_idx += 1
        parts = [get_canonical_name(p.strip()) for p in str(row.get('Teilnehmer','')).split(',') if p.strip()]
        winners = [get_canonical_name(x) for x in parse_list(row, 'Winner')]
        losers = [get_canonical_name(x) for x in parse_list(row, 'Loser')]
        match_date = row['Datum']
        
        for name in parts:
            if any(re.search(rf'\(w/.*{re.escape(name)}.*\)', p, flags=re.IGNORECASE) for p in parts): continue
            
            if name not in wrestlers:
                wrestlers[name] = {'matches': [], 'wins': 0, 'losses': 0, 'draws': 0, 'ratings': [], 'opponents': {}, 'partners': {}}
            
            stats = wrestlers[name]
            result = 'draw'
            if name in winners: result = 'win'; stats['wins'] += 1
            elif name in losers: result = 'loss'; stats['losses'] += 1
            else: stats['draws'] += 1
            
            if result == 'win': opps = [p for p in losers if p!=name]; parts_p = [p for p in winners if p!=name]
            elif result == 'loss': opps = [p for p in winners if p!=name]; parts_p = [p for p in losers if p!=name]
            else: opps = [p for p in parts if p!=name]; parts_p = []
            
            for o in opps: stats['opponents'][o] = stats['opponents'].get(o, 0) + 1
            for p in parts_p: stats['partners'][p] = stats['partners'].get(p, 0) + 1
            
            rating = row.get('Bewertung (Numerisch)', 0)
            if pd.notna(rating): stats['ratings'].append(rating)
            match_link = enhanced_smart_link(row['Match'], row['Teilnehmer'])
            
            stats['matches'].append({
                'date': match_date, 'event': row['Show'], 'match': row['Match'], 
                'match_link': match_link, 'result': result, 'rating': rating,
                'finish': row.get('Finish', ''), 'event_file': f"{match_date.strftime('%Y-%m-%d')} - {row['Show']}",
                'winners': winners, 'losers': losers, 'pos': match_idx
            })

    index_lines = ["---\ndg-publish: true\npermalink: /wrestler/\ntags: [index, wrestler]\n---\n# Wrestler\n| Wrestler | Matches | Wins | Losses | Draws | Win % | Ø Rating |\n|---|---|---|---|---|---|---|"]
    
    for name, stats in sorted(wrestlers.items()):
        # Skip aliases — sie bekommen keine eigene Seite (der Canonical-Name sammelt alle Stats)
        if name in WRESTLER_ALIASES:
            continue
        total = stats['wins'] + stats['losses'] + stats['draws']
        win_pct = (stats['wins']/total*100) if total>0 else 0
        avg_rat = sum(stats['ratings'])/len(stats['ratings']) if stats['ratings'] else 0
        
        chart_url = generate_donut_chart(name, stats['wins'], stats['losses'], stats['draws'])
        opps_sorted = sorted(stats['opponents'].items(), key=lambda x:x[1], reverse=True)[:5]
        parts_sorted = sorted(stats['partners'].items(), key=lambda x:x[1], reverse=True)[:5]
        last_5 = sorted(stats['matches'], key=lambda x: (x['date'], x['pos']), reverse=True)[:5]
        top_5 = sorted(stats['matches'], key=lambda x: x['rating'], reverse=True)[:5]

        img_url = f"https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/{name.replace(' ', '_')}.png"
        
        # Form Icons
        form_icons = "".join(["✅" if m['result']=='win' else "❌" if m['result']=='loss' else "⚪️" for m in reversed(last_5)])
        
        # Facts
        nemesis = max(stats['opponents'], key=stats['opponents'].get) if stats['opponents'] else "Niemand"
        partner = max(stats['partners'], key=stats['partners'].get) if stats['partners'] else "Einzelgänger"
        best_match = top_5[0] if top_5 else None
        
        yaml_dict = {
            "dg-publish": "true", "permalink": f"/wrestler/{slugify(name)}/", "title": name, "tags": ["wrestler"],
            "img": img_url, "matches": total, "wins": stats['wins'], "losses": stats['losses'],
            "draws": stats['draws'], "win_percent": float(f"{win_pct:.1f}"), "avg_rating": float(f"{avg_rat:.2f}"),
        }
        
        fname = os.path.join(PATHS['wrestler'], f"{name}.md")
        with open(fname, "w", encoding="utf-8") as f:
            f.write("---\n"); yaml.dump(yaml_dict, f, sort_keys=False); f.write("---\n\n")
            f.write(f"# {name}\n\n")
            # Alter-Ego Hinweis
            if name in CANONICAL_ALIASES:
                alias_list = ", ".join(CANONICAL_ALIASES[name])
                f.write(f"> \u2139\ufe0f **Auch bekannt als:** {alias_list}\n\n")
            info = edits_dict.get(name, {})
            f.write(f"<table><tr><td><img src=\"{img_url}\" width=\"280\"></td>")
            f.write(f"<td><b>Height:</b> {info.get('Height','N/A')}<br><b>Weight:</b> {info.get('Weight','N/A')}<br><b>Finisher:</b> {info.get('Finisher','N/A')}</td></tr></table>\n\n")
            
            f.write(f"## Karriere-Statistiken\n| Matches | Siege | Niederlagen | Draws | Win % | Ø Rating |\n|---|---|---|---|---|---|\n")
            f.write(f"| {total} | {stats['wins']} | {stats['losses']} | {stats['draws']} | {win_pct:.1f}% | {avg_rat:.2f} |\n\n")
            
            # ADVANCED STATS LAYOUT (3 Columns)
            f.write("### Advanced Stats\n")
            f.write("| Record | Form | Facts |\n|:---:|---|---|\n")
            
            # Form List
            form_text = f"**{form_icons}**<br>"
            for m in last_5:
                date_s = m['date'].strftime('%Y-%m-%d')
                event_link = f"[[Events/{m['event_file']}\|{m['event']}]]"
                res_label = m['result'].title() # Win/Loss/Draw
                
                # Format: Win: Match in Event (Date)
                line = f"**{res_label}:** {m['match']} in {event_link} ({date_s})"
                form_text += f"{line}<br>"
            
            # Facts Text
            facts_text = f"**Nemesis:** [[Wrestler/{nemesis}\|{nemesis}]]<br>**Partner:** [[Wrestler/{partner}\|{partner}]]"
            if best_match: facts_text += f"<br>**Best Match:** {best_match['rating']}% vs. {best_match['match']}"
            
            f.write(f"| {chart_url} | {form_text} | {facts_text} |\n\n")

            if opps_sorted:
                f.write("## Häufigste Gegner\n")
                for o, c in opps_sorted: f.write(f"- [[Wrestler/{o}\|{o}]] ({c}x)\n")
            
            if parts_sorted:
                f.write("\n## Häufigste Partner\n")
                for o, c in parts_sorted: f.write(f"- [[Wrestler/{o}\|{o}]] ({c}x)\n")

            f.write("\n## Top Matches\n")
            for m in top_5:
                f.write(f"- {m['rating']}%: {m['match_link']} in [[Events/{m['event_file']}\|{m['event']}]] ({m['date'].strftime('%Y-%m-%d')})\n")

        index_lines.append(f"| [[Wrestler/{name}\|{name}]] | {total} | {stats['wins']} | {stats['losses']} | {stats['draws']} | {win_pct:.1f}% | {avg_rat:.2f} |")

    with open(os.path.join(NOTES_BASE_DIR, "Wrestler.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))
    print("✅ Wrestler fertig.")

# =============================================================================
# TEIL 4 & 5 & 6 (UNCHANGED)
# =============================================================================
def part4_global():
    print("4. Globale Statistiken...")
    if not os.path.exists(PFAD_EXCEL_OUTPUT): return
    df = pd.read_excel(PFAD_EXCEL_OUTPUT); df['Datum'] = pd.to_datetime(df['Datum'])
    df['Jahr'] = df['Datum'].dt.year
    os.makedirs(PATHS['stats'], exist_ok=True)
    season_regex = r'(S\d{2})(?=[\s\-_]*E?\d{1,3}|[^A-Za-z0-9]|$)'
    s = pd.Series(pd.NA, index=df.index, dtype="object")
    comb = df[['Show']].astype(str).agg(' | '.join, axis=1)
    s = s.fillna(comb.str.extract(season_regex, flags=re.I, expand=False).str.upper())
    df['Saison'] = s
    lines = ["---\ndg-publish: true\npermalink: /statistiken/globale-statistiken/\ntags: [statistik]\n---\n# Globale Statistiken\n"]
    m_year = df.groupby('Jahr').size()
    lines.append("## Matches pro Jahr\n| Jahr | Matches |\n|---|---|")
    for y, c in m_year.items(): lines.append(f"| {int(y)} | {c} |")
    if df['Saison'].notna().any():
        lines.append("\n## Matches pro Saison\n| Saison | Matches |\n|---|---|")
        for sa, c in df.groupby('Saison').size().items(): lines.append(f"| {sa} | {c} |")
    winners = []
    for w in df['Winner'].dropna(): winners.extend([x.strip() for x in str(w).split(',') if x.strip()])
    win_counts = pd.Series(winners).value_counts().head(10)
    lines.append("\n## Top 10 Siege\n| Wrestler | Siege |\n|---|---|")
    for w, c in win_counts.items(): lines.append(f"| [[Wrestler/{w}\|{w}]] | {c} |")
    if 'Bewertung (Numerisch)' in df.columns:
        top25 = df.sort_values('Bewertung (Numerisch)', ascending=False).head(25)
        with open(os.path.join(PATHS['stats'], "Top 25 Matches.md"), "w", encoding="utf-8") as f:
            f.write("---\ndg-publish: true\npermalink: /statistiken/top-25-matches/\n---\n# Top 25 Matches\n| Date | Match | Rating |\n|---|---|---|\n")
            for _, row in top25.iterrows():
                f.write(f"| {row['Datum'].strftime('%Y-%m-%d')} | [[Events/{row['Datum'].strftime('%Y-%m-%d')} - {row['Show']}\|{row['Match']}]] | {row.get('Bewertung (Numerisch)')} |\n")
    with open(os.path.join(PATHS['stats'], "Globale Statistiken.md"), "w", encoding="utf-8") as f: f.write("\n".join(lines))
    print("✅ Globale Stats fertig.")

def part5_championships():
    print("5. Championships...")
    if not os.path.exists(PFAD_EXCEL_OUTPUT): return
    
    # Read Excel preserving all columns
    df = pd.read_excel(PFAD_EXCEL_OUTPUT); df.columns = [c.strip() for c in df.columns]
    df['Datum'] = pd.to_datetime(df['Datum'])
    os.makedirs(PATHS['championships'], exist_ok=True)
    
    champ_matches = {}
    for index, row in df.iterrows():
        title = normalize_title({'name': row['Match'], 'Championship': row.get('Championship')})
        if not title: continue
        winner_str = str(row.get('Winner', '')).strip()
        if winner_str.lower() == 'nan': winner_str = '??'
        champ_matches.setdefault(title, []).append({
            "name": str(row['Match']),
            "finish": str(row.get('Finish','')),
            "date": row['Datum'].strftime("%Y-%m-%d"),
            "event_file": f"{row['Datum'].strftime('%Y-%m-%d')} - {row['Show']}",
            "winner_str": winner_str,
            "_seq": index
        })

    for title, matches in champ_matches.items():
        matches.sort(key=lambda x: (x['date'], x['_seq']))
        slug = slugify(title)
        
        lines = [f"---\ndg-publish: true\npermalink: /championships/{slug}/\ntitle: {title}\n---\n"]
        img = f"https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/{title.replace(' ', '_')}.png"
        lines.append(f"### {title}\n<img src=\"{img}\" width=\"700\">\n")
        
        # Build reign list using the Winner column (reliable from XML/Excel)
        reigns = []
        current_raw = None
        reign_start = None
        start_event = None
        run_defs = {}
        
        for m in matches:
            winner_str = m['winner_str']
            date = m['date']
            event_file = m['event_file']
            match_lc = m['name'].lower()
            finish_lc = m['finish'].lower()
            
            is_vacant_match = "(vakant)" in match_lc or "(vacant)" in match_lc
            is_champ_match = "(c)" in match_lc
            
            title_change = False
            if current_raw is not None and winner_str != current_raw:
                if not any(x in finish_lc for x in ["dq", "count out", "draw", "no contest", "double ko"]):
                    title_change = True
            
            if title_change:
                reigns.append((current_raw, reign_start, start_event, date, event_file, run_defs.get(current_raw+str(reign_start), 0)))
                if is_vacant_match:
                    reigns.append(("Vacant", date, event_file, date, event_file, 0))
                current_raw = winner_str
                reign_start = date
                start_event = event_file
                run_defs[current_raw+str(reign_start)] = 0
            elif current_raw is None:
                current_raw = winner_str
                reign_start = date
                start_event = event_file
                run_defs[current_raw+str(reign_start)] = 0
            elif is_vacant_match:
                reigns.append((current_raw, reign_start, start_event, date, event_file, run_defs.get(current_raw+str(reign_start), 0)))
                reigns.append(("Vacant", date, event_file, date, event_file, 0))
                current_raw = winner_str
                reign_start = date
                start_event = event_file
                run_defs[current_raw+str(reign_start)] = 0
            elif is_champ_match:
                run_defs[current_raw+str(reign_start)] = run_defs.get(current_raw+str(reign_start), 0) + 1
        
        if current_raw is not None:
            reigns.append((current_raw, reign_start, start_event, None, None, run_defs.get(current_raw+str(reign_start), 0)))
        
        # Calculate champion statistics
        wstats = {}
        for r in reigns:
            champ_raw = r[0]
            if champ_raw in ("Vacant", "??"):
                continue
            if champ_raw not in wstats:
                wstats[champ_raw] = {"reigns": 0, "defenses": 0, "total_days": 0, "longest": 0}
            ws = wstats[champ_raw]
            ws["reigns"] += 1
            ws["defenses"] += r[5]
            if r[3] is not None:
                duration = (datetime.fromisoformat(r[3]) - datetime.fromisoformat(r[1])).days
            else:
                duration = (datetime.now() - datetime.fromisoformat(r[1])).days
            ws["total_days"] += duration
            if duration > ws["longest"]:
                ws["longest"] = duration
        
        current_champion_raw = reigns[-1][0] if reigns else "??"
        current_champion_link = format_champion_link(current_champion_raw)
        
        most_reigns = max(wstats.items(), key=lambda x: x[1]['reigns']) if wstats else None
        longest_reign = max(wstats.items(), key=lambda x: x[1]['longest']) if wstats else None
        most_defenses = max(wstats.items(), key=lambda x: x[1]['defenses']) if wstats else None
        
        is_tag = "Tag Team" in title
        is_trios = "Trios" in title
        champ_type_label = "(Singles)"
        if is_tag: champ_type_label = "(Tag Team)"
        if is_trios: champ_type_label = "(Trios)"
        
        # Current Champion(s)
        lines.append(f"## 👑 Aktuelle Champions {champ_type_label}")
        lines.append(f"**{current_champion_link}**\n")
        
        # Statistics
        lines.append("## 📊 Statistiken")
        lines.append('<table>')
        lines.append('<thead><tr><th>Kategorie</th><th>Wert</th></tr></thead>')
        lines.append('<tbody>')
        total_reigns = len([r for r in reigns if r[0] not in ('Vacant', '??')])
        unique_champs = len([r for r in wstats.items()])
        vacant_count = len([r for r in reigns if r[0] == 'Vacant'])
        # Additional stats
        first_reign = None
        for r in reigns:
            if r[0] not in ('Vacant', '??'):
                first_reign = r
                break
        shortest_reign = min(wstats.items(), key=lambda x: x[1]['longest']) if wstats else None
        # Compute reign durations (non-vacant, non-current)
        reign_durations = []
        successful_defenses_total = 0
        for r in reigns:
            if r[0] not in ('Vacant', '??') and r[3] is not None:
                dur = (datetime.fromisoformat(r[3]) - datetime.fromisoformat(r[1])).days
                reign_durations.append(dur)
            if r[5] > 0:
                successful_defenses_total += r[5]
        avg_reign = sum(reign_durations) // len(reign_durations) if reign_durations else 0
        # Current reign counter
        current_reign = reigns[-1] if reigns else None
        current_reign_days = ""
        if current_reign and current_reign[0] not in ('Vacant', '??') and current_reign[3] is None:
            current_reign_days = (datetime.now() - datetime.fromisoformat(current_reign[1])).days
        lines.append(f'<tr><td><strong>Insgesamt Regentschaften</strong></td><td>{total_reigns}</td></tr>')
        lines.append(f'<tr><td><strong>Verschiedene Champions</strong></td><td>{unique_champs}</td></tr>')
        lines.append(f'<tr><td><strong>Vakante Phasen</strong></td><td>{vacant_count}</td></tr>')
        if first_reign:
            lines.append(f'<tr><td><strong>Erster Champion</strong></td><td>{format_champion_link(first_reign[0])} ({first_reign[1]})</td></tr>')
        lines.append(f'<tr><td><strong>⌀ Regentschaftsdauer</strong></td><td>{avg_reign} Tage</td></tr>')
        if longest_reign:
            lines.append(f'<tr><td><strong>Längste Regentschaft</strong></td><td>{format_champion_link(longest_reign[0])} ({longest_reign[1]["longest"]} Tage)</td></tr>')
        if shortest_reign and shortest_reign[1]['longest'] > 0:
            lines.append(f'<tr><td><strong>Kürzeste Regentschaft</strong></td><td>{format_champion_link(shortest_reign[0])} ({shortest_reign[1]["longest"]} Tage)</td></tr>')
        if most_reigns:
            lines.append(f'<tr><td><strong>Meiste Regentschaften</strong></td><td>{format_champion_link(most_reigns[0])} ({most_reigns[1]["reigns"]}x)</td></tr>')
        if most_defenses:
            lines.append(f'<tr><td><strong>Meiste Verteidigungen</strong></td><td>{format_champion_link(most_defenses[0])} ({most_defenses[1]["defenses"]} Verteidigungen)</td></tr>')
        # Title match stats
        defense_pct = round(successful_defenses_total / (total_reigns + successful_defenses_total) * 100) if (total_reigns + successful_defenses_total) > 0 else 0
        lines.append(f'<tr><td><strong>Titelmatches gesamt</strong></td><td>{total_reigns + successful_defenses_total}</td></tr>')
        lines.append(f'<tr><td><strong>Erfolgreiche Verteidigungen</strong></td><td>{successful_defenses_total} ({defense_pct}%)</td></tr>')
        if current_reign_days:
            lines.append(f'<tr><td><strong>Aktuelle Regentschaft</strong></td><td>{format_champion_link(current_reign[0])} — Tag {current_reign_days} 🔥</td></tr>')
        lines.append('</tbody>')
        lines.append('</table>')
        lines.append("")
        
        # Champion stats breakdown
        lines.append("### Champion-Statistiken")
        lines.append('<table>')
        lines.append('<thead><tr><th>Champion</th><th>Regentschaften</th><th>Verteidigungen</th><th>Längste Regentschaft</th><th>Gesamttage</th></tr></thead>')
        lines.append('<tbody>')
        for champion_raw, ws in sorted(wstats.items(), key=lambda x: -x[1]['reigns']):
            clink = format_champion_link(champion_raw)
            lines.append(f'<tr><td>{clink}</td><td>{ws["reigns"]}</td><td>{ws["defenses"]}</td><td>{ws["longest"]} Tage</td><td>{ws["total_days"]} Tage</td></tr>')
        lines.append('</tbody>')
        lines.append('</table>')
        lines.append("")
        
        # Title history
        lines.append("## Title History")
        lines.append('<table>')
        lines.append('<thead><tr><th>Champion</th><th>Start</th><th>Event</th><th>Ende</th><th>Dauer</th><th>Verteidigungen</th></tr></thead>')
        lines.append('<tbody>')
        for r in reigns:
            champ_raw = r[0]
            if champ_raw == "Vacant":
                champ_link = "Vacant"
            else:
                champ_link = format_champion_link(champ_raw)
            if r[3] is not None:
                dur = f"{(datetime.fromisoformat(r[3]) - datetime.fromisoformat(r[1])).days} Tage"
                end_str = r[3]
            else:
                dur = "aktuell"
                end_str = "Current"
            event_link = f"[[Events/{r[2]}\|{r[2]}]]"
            lines.append(f"<tr><td>{champ_link}</td><td>{r[1]}</td><td>{event_link}</td><td>{end_str}</td><td>{dur}</td><td>{r[5]}</td></tr>")
        lines.append('</tbody>')
        lines.append('</table>')
        
        with open(os.path.join(PATHS['championships'], f"{slug}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    return champ_matches

def part6_home(champ_data):
    print("6. Generiere Home.md...")
    if not os.path.exists(PFAD_EXCEL_OUTPUT): return
    df = pd.read_excel(PFAD_EXCEL_OUTPUT); df['Datum'] = pd.to_datetime(df['Datum'])
    events_unique = df.drop_duplicates(subset=['Datum', 'Show']).sort_values('Datum', ascending=False).head(5)
    current_champs = []
    if champ_data:
        for title, matches in champ_data.items():
            matches.sort(key=lambda x: (x['date'], x['_seq']))
            current = ""
            for m in matches:
                winner = m['winner_str']
                match_lc = m['name'].lower()
                is_vacant = ('(vakant)' in match_lc) or ('(vacant)' in match_lc)
                if is_vacant:
                    current = ""
                if not winner:
                    continue
                if is_vacant or not current:
                    current = winner
                elif winner != current:
                    finish_lc = m['finish'].lower()
                    if not any(x in finish_lc for x in ['dq', 'count out', 'draw', 'no contest']):
                        current = winner
            icon = "🏆"
            if "Tag" in title: icon = "👥"
            if "Trios" in title: icon = "👪"
            if "Women" in title: icon = "👩"
            slug = slugify(title)
            cur_link = format_champion_link(current) if current else "Vacant"
            current_champs.append(f"| {icon} | [[Championships/{slug}\|{title}]] | **{cur_link}** |")

    current_year = datetime.now().year
    df_year = df[df['Datum'].dt.year == current_year]
    if df_year.empty: current_year -= 1; df_year = df[df['Datum'].dt.year == current_year]
    winners = []
    for w in df_year['Winner'].dropna(): winners.extend([x.strip() for x in str(w).split(',') if x.strip()])
    top_wrestlers = pd.Series(winners).value_counts().head(5)

    home_file = os.path.join(NOTES_BASE_DIR, "Home.md")
    with open(home_file, "w", encoding="utf-8") as f:
        f.write("---\ndg-publish: true\npermalink: /home/\ntitle: Home\nnoteIcon: 🏠\n---\n\n")
        base_img_url = "https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/"
        f.write('<div style="text-align: center;">\n')
        f.write(f'  <img src="{base_img_url}ChokeSlam.png" width="400" alt="Choke Slam Wrestling">\n')
        f.write('  <br><br>\n')
        f.write('  <div style="display: flex; justify-content: center; gap: 20px;">\n')
        f.write(f'    <img src="{base_img_url}ChokeSlam_MM.png" width="100" alt="Militanter Mummenschanz">\n')
        f.write(f'    <img src="{base_img_url}ChokeSlam_SRR.png" width="100" alt="Saint Rebel Radicalz">\n')
        f.write(f'    <img src="{base_img_url}ChokeSlam_SnS.png" width="100" alt="Sweet \'n Sour Elite">\n')
        f.write('  </div>\n</div>\n\n')
        f.write("# 🏠 Choke Slam Wrestling\n\nWillkommen im **Digital Garden** von Choke Slam Wrestling! Hier findest du alle Ergebnisse, Statistiken und Historien unseres Universums.\n\n")
        f.write("## 📅 Die letzten Events\n| Datum | Show | Main Event |\n|---|---|---|\n")
        for _, row in events_unique.iterrows():
            date_str = row['Datum'].strftime('%Y-%m-%d'); show_name = row['Show']
            main_event_match = df[(df['Datum'] == row['Datum']) & (df['Show'] == show_name)].iloc[-1]
            me_name = main_event_match['Match']
            filename = f"{date_str} - {show_name}"; show_clean = show_name.replace("|", "-"); me_clean = me_name.replace("|", "-")
            f.write(f"| {date_str} | [[Events/{filename}\|{show_clean}]] | {me_clean} |\n")
        f.write("\n## 🏆 Aktuelle Champions\n| | Titel | Champion |\n|---|---|---|\n")
        for line in current_champs: f.write(line + "\n")
        f.write(f"\n## 🔥 Top Performer {current_year}\n| Wrestler | Siege |\n|---|---|\n")
        for w, c in top_wrestlers.items(): f.write(f"| [[Wrestler/{w}\|{w}]] | {c} |\n")
        f.write("\n---\n### 🧭 Navigation\n- [[Events\|📅 Alle Events]]\n- [[Wrestler\|🤼 Roster & Stats]]\n- [[Championships\|🏆 Titelhistorien]]\n- [[Statistiken\|📊 Globale Statistiken]]\n")
    print("✅ Home.md generiert.")

def main():
    print("🚀 START: Wrestling Manager COMPLETE")
    if part1_xml_to_excel():
        part2_events()
        part3_wrestlers() # Poster Generation included in part2_events but called here as flow
        part4_global()
        champ_data = part5_championships()
        part6_home(champ_data)
        # PWI 500 Ranking
        print("7. PWI 500 Ranking...")
        import subprocess, sys
        env = os.environ.copy()
        env["CHOKE_SLAM_EXCEL"] = os.path.abspath(PFAD_EXCEL_OUTPUT)
        env["CHOKE_SLAM_REPO"] = GIT_REPO_DIR
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "chokeslam_pwi500.py")],
                       env=env, check=False)
        if os.environ.get("CHOKE_SLAM_SKIP_PUSH") == "1":
            print("Git upload deferred to the canonical refresh wrapper.")
        else:
            push_to_github()

if __name__ == "__main__": main()
