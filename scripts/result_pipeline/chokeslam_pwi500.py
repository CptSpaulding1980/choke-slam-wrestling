#!/usr/bin/env python3
"""
Choke Slam PWI Power Ranking Generator
Erstellt eine HTML-Statistikseite mit Wrestler-Rankings, 
Championship-Historien und Match-Statistiken.

Pfade via Env (von choke_slam_manager.py oder Cron gesetzt):
  CHOKE_SLAM_EXCEL  — Pfad zur Choke_Slam_export.xlsx (default: ./Choke_Slam_export.xlsx)
  CHOKE_SLAM_REPO   — Pfad zum choke-slam-wrestling Repo (default: ~/repos/choke-slam-wrestling)
"""

import pandas as pd
import re
import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────────────────
EXCEL_FILE = Path(os.environ.get(
    "CHOKE_SLAM_EXCEL",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Choke_Slam_export.xlsx")
))
GIT_REPO_DIR = Path(os.environ.get(
    "CHOKE_SLAM_REPO",
    os.path.expanduser("~/repos/choke-slam-wrestling")
))
OUTPUT_FILE = GIT_REPO_DIR / "src/site/notes/Statistiken" / "PWI Power Ranking.md"

CHAMP_BONUS = {
    "Choke Slam World Championship": 20,
    "Choke Slam International Championship": 15,
    "Choke Slam Womens Championship": 15,
    "Choke Slam Tag Team Championship": 10,
    "Choke Slam Trios Championship": 8,
}

def normalize(name):
    if pd.isna(name) or name == '':
        return None
    return str(name).strip()

def compute_stats(df):
    stats = defaultdict(lambda: {
        'wins': 0, 'losses': 0, 'draws': 0, 
        'total_rating': 0, 'rating_count': 0, 'match_count': 0,
        'opponents': defaultdict(int), 'championships': defaultdict(int),
        'title_matches': 0, 'title_wins': 0
    })
    
    tag_stats = defaultdict(lambda: {
        'wins': 0, 'losses': 0, 'draws': 0,
        'total_rating': 0, 'rating_count': 0, 'match_count': 0
    })
    
    for _, row in df.iterrows():
        rating = row.get('Bewertung (Numerisch)', 0)
        if pd.isna(rating): rating = 0
        
        draw_val = row['Draw'] if pd.notna(row['Draw']) and row['Draw'] != '' else None
        championship = normalize(row['Championship'])
        is_title = row.get('IsChampionship', False)
        
        winners = [w.strip() for w in str(row['Winner']).split(',') if w.strip()] if pd.notna(row['Winner']) and row['Winner'] != '' else []
        losers = [l.strip() for l in str(row['Loser']).split(',') if l.strip()] if pd.notna(row['Loser']) and row['Loser'] != '' else []
        
        if draw_val and not winners:
            draw_parts = [d.strip() for d in draw_val.split(',') if d.strip()]
            for p in draw_parts:
                stats[p]['draws'] += 1
                stats[p]['match_count'] += 1
                if rating > 0:
                    stats[p]['total_rating'] += rating
                    stats[p]['rating_count'] += 1
            
            if len(draw_parts) >= 4:
                half = len(draw_parts) // 2
                t1 = ' & '.join(sorted(draw_parts[:half]))
                t2 = ' & '.join(sorted(draw_parts[half:]))
                tag_stats[t1]['draws'] += 1; tag_stats[t1]['match_count'] += 1
                tag_stats[t2]['draws'] += 1; tag_stats[t2]['match_count'] += 1
        
        elif winners:
            # Rumbles can name the winner while reporting anonymous opponents.
            # Count the real win without inventing opponent names or losses.
            for w in winners:
                stats[w]['wins'] += 1; stats[w]['match_count'] += 1
                if rating > 0: stats[w]['total_rating'] += rating; stats[w]['rating_count'] += 1
                for l in losers: stats[w]['opponents'][l] += 1
                if is_title: stats[w]['title_wins'] += 1
            
            for l in losers:
                stats[l]['losses'] += 1; stats[l]['match_count'] += 1
                if rating > 0: stats[l]['total_rating'] += rating; stats[l]['rating_count'] += 1
                for w in winners: stats[l]['opponents'][w] += 1
            
            if is_title:
                for w in winners:
                    stats[w]['title_matches'] += 1
                    if championship: stats[w]['championships'][championship] += 1
                for l in losers:
                    stats[l]['title_matches'] += 1
                    if championship: stats[l]['championships'][championship] += 1
            
            wset = frozenset(w.lower() for w in winners)
            lset = frozenset(l.lower() for l in losers)
            if len(wset) == 2:
                wtag = ' & '.join(sorted(winners, key=str.lower))
                tag_stats[wtag]['wins'] += 1; tag_stats[wtag]['match_count'] += 1
                if rating > 0: tag_stats[wtag]['total_rating'] += rating; tag_stats[wtag]['rating_count'] += 1
            if len(lset) == 2:
                ltag = ' & '.join(sorted(losers, key=str.lower))
                tag_stats[ltag]['losses'] += 1; tag_stats[ltag]['match_count'] += 1
                if rating > 0: tag_stats[ltag]['total_rating'] += rating; tag_stats[ltag]['rating_count'] += 1
    
    return stats, tag_stats

def chronological_title_matches(df):
    """Date, numeric season/episode, then original XML/XLSX match order.

    Unparseable historical names retain their positions in each date group;
    only parseable show slots are reordered. No alphabetical/reverse tie-break.
    """
    matches = df[df['IsChampionship'] == True].copy()
    matches['Datum'] = pd.to_datetime(matches['Datum'], errors='coerce')
    matches = matches.sort_values('Datum', kind='stable').reset_index(drop=True)
    order = list(range(len(matches)))
    for _, group in matches.groupby('Datum', sort=False, dropna=False):
        keys = {}
        for pos, show in group['Show'].items():
            key = re.match(r'^S(\d+)E(\d+)(?:\D|$)', str(show))
            if key:
                keys[pos] = tuple(map(int, key.groups()))
        slots = list(keys)
        for slot, pos in zip(slots, sorted(slots, key=keys.get)):
            order[slot] = pos
    return matches.iloc[order]


def get_current_champions(df):
    champs = {}
    champ_df = chronological_title_matches(df)
    
    for champ_name in CHAMP_BONUS:
        relevant = champ_df[champ_df['Championship'] == champ_name]
        if len(relevant) == 0: continue
        winner = normalize(relevant.iloc[-1]['Winner'])
        if winner: champs[champ_name] = winner
    return champs

def compute_ranking(stats, current_champs):
    ranking = []
    for name, s in stats.items():
        if s['match_count'] < 3: continue
        bonus = 0; titles = []
        for cname, champ in current_champs.items():
            if name.lower() == champ.lower():
                bonus = max(bonus, CHAMP_BONUS.get(cname, 0))
                titles.append(cname.replace('Choke Slam ', ''))
        avg_r = s['total_rating'] / s['rating_count'] if s['rating_count'] > 0 else 0
        score = (s['wins'] * 2) + s['draws'] - s['losses'] + avg_r * 0.3 + bonus
        ranking.append({
            'name': name, 'wins': s['wins'], 'losses': s['losses'], 'draws': s['draws'],
            'win_pct': (s['wins'] / s['match_count'] * 100) if s['match_count'] > 0 else 0,
            'avg_rating': avg_r, 'score': score, 'titles': titles, 'match_count': s['match_count']
        })
    ranking.sort(key=lambda x: x['score'], reverse=True)
    return ranking

def compute_tag_ranking(tag_stats):
    ranking = []
    for name, s in tag_stats.items():
        if s['match_count'] < 2: continue
        avg_r = s['total_rating'] / s['rating_count'] if s['rating_count'] > 0 else 0
        score = (s['wins'] * 2) + s['draws'] - s['losses'] + avg_r * 0.3
        ranking.append({
            'name': name, 'wins': s['wins'], 'losses': s['losses'], 'draws': s['draws'],
            'win_pct': (s['wins'] / s['match_count'] * 100) if s['match_count'] > 0 else 0,
            'avg_rating': avg_r, 'score': score, 'match_count': s['match_count']
        })
    ranking.sort(key=lambda x: x['score'], reverse=True)
    return ranking

def get_top_matches(df, n=25):
    top = df[df['Bewertung (Numerisch)'].notna()].copy()
    return top.sort_values('Bewertung (Numerisch)', ascending=False).head(n)

def get_championship_history(df):
    title_matches = chronological_title_matches(df)
    
    history = {}
    for _, row in title_matches.iterrows():
        champ = normalize(row['Championship'])
        if not champ: continue
        winner = normalize(row['Winner']); loser = normalize(row['Loser'])
        if not winner or not loser: continue
        date = row['Datum'].strftime('%Y-%m-%d') if pd.notna(row['Datum']) else '?'
        if champ not in history: history[champ] = []
        history[champ].append({'date': date, 'winner': winner, 'loser': loser,
                               'show': normalize(row['Show']), 'rating': row.get('Bewertung (Numerisch)', 0)})
    return history

def generate_markdown(ranking, tag_ranking, current_champs, top_matches, champ_history, df, season):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    total = len(df)
    
    # Frontmatter
    out = []
    out.append("---")
    out.append("dg-publish: true")
    out.append("permalink: /statistiken/pwi-power-ranking/")
    out.append('title: "PWI Power Ranking"')
    out.append('noteIcon: "🏆"')
    out.append("---")
    out.append("")
    out.append(f"# 🏆 PWI Power Ranking – {season}")
    out.append("")
    out.append(f"> **Stand:** {now} | **Matches:** {total} | **Wrestler geranked:** {len(ranking)} | **Events:** {df['Show'].nunique()}")
    out.append("")
    out.append("**Scoring:** PWI Punkte = (Wins × 2) + Draws − Losses + (Ø Rating × 0.3) + Championship Bonus")
    out.append("")
    out.append("Championship Bonus: World +20 · International/Women's +15 · Tag Team +10 · Trios +8")
    out.append("")
    
    # Singles Top 50
    out.append("## 🥇 Singles Top 50")
    out.append("")
    out.append("| # | Wrestler | W | L | D | Win% | Ø★ | Pts |")
    out.append("|:-:|----------|:-:|:-:|:-:|----:|----:|----:|")
    for i, w in enumerate(ranking[:50], 1):
        badge = " 🏆" if w['titles'] else ""
        out.append(f"| {i} | {w['name']}{badge} | {w['wins']} | {w['losses']} | {w['draws']} | {w['win_pct']:.0f}% | {w['avg_rating']:.0f} | {w['score']:.0f} |")
    out.append("")
    
    # Current Champions
    out.append("## 🏆 Aktuelle Champions")
    out.append("")
    out.append("| Titel | Champion | Bonus |")
    out.append("|-------|----------|:-----:|")
    for cname, bonus in CHAMP_BONUS.items():
        cur = current_champs.get(cname, "—")
        out.append(f"| {cname} | **{cur}** | +{bonus} |")
    out.append("")
    
    # Tag Teams
    out.append("## 👥 Tag Teams Top 25")
    out.append("")
    out.append("| # | Team | W | L | D | Win% | Ø★ | Pts |")
    out.append("|:-:|------|:-:|:-:|:-:|----:|----:|----:|")
    for i, t in enumerate(tag_ranking[:25], 1):
        out.append(f"| {i} | {t['name']} | {t['wins']} | {t['losses']} | {t['draws']} | {t['win_pct']:.0f}% | {t['avg_rating']:.0f} | {t['score']:.0f} |")
    out.append("")
    
    # Top Matches
    out.append("## ⭐ Top 25 Matches")
    out.append("")
    out.append("| Datum | Show | Match | Rating | Score |")
    out.append("|-------|------|-------|--------|------:|")
    for _, m in top_matches.iterrows():
        out.append(f"| {m['Datum']} | {m['Show']} | {m['Match']} | {m.get('Bewertung (Sterne)', '')} | {m.get('Bewertung (Numerisch)', '')} |")
    out.append("")
    
    # Championship History
    out.append("## 📜 Championship History")
    out.append("")
    for cname in CHAMP_BONUS:
        if cname not in champ_history: continue
        out.append(f"### 🏆 {cname}")
        out.append("")
        out.append("| Datum | Winner | Loser | Show |")
        out.append("|-------|--------|-------|------|")
        for h in champ_history[cname]:
            out.append(f"| {h['date']} | **{h['winner']}** | {h['loser']} | {h['show']} |")
        out.append("")
    
    # Win/Loss distribution
    win_counts = sum(1 for w in ranking if w['win_pct'] >= 50)
    out.append("## 📊 Statistiken")
    out.append("")
    out.append(f"- **Winning Record (≥50%):** {win_counts} Wrestler")
    out.append(f"- **Losing Record (<50%):** {len(ranking) - win_counts} Wrestler")
    out.append("")
    out.append("### Top 5 – Meiste Siege")
    out.append("| Wrestler | Wins |")
    out.append("|----------|:----:|")
    for w in sorted(ranking, key=lambda x: x['wins'], reverse=True)[:5]:
        out.append(f"| {w['name']} | {w['wins']} |")
    out.append("")
    
    out.append("---")
    out.append("*Auto-generiert vom Choke Slam PWI Power Ranking Generator*")
    out.append(f"*Stand: {now}*")
    
    return "\n".join(out)

def main():
    print("Choke Slam PWI Power Ranking Generator")
    print("=" * 50)
    
    if not EXCEL_FILE.exists():
        print(f"❌ Excel nicht gefunden: {EXCEL_FILE}")
        print(f"   (cwd={os.getcwd()})")
        return False
    
    df = pd.read_excel(EXCEL_FILE)
    # Standalone XLSX inputs may bypass the manager's canonical result import.
    # Normalize identity columns only; match names/finish text stay historical.
    for column in ('Teilnehmer', 'Winner', 'Loser', 'Draw'):
        if column in df:
            df[column] = df[column].map(
                lambda value: ', '.join(
                    'Big Van Vader' if name.strip() == 'Vader' else name.strip()
                    for name in str(value).split(',')
                ) if pd.notna(value) else value
            )
    df['Datum'] = pd.to_datetime(df['Datum'], errors='coerce')
    
    # Nur aktuelle Saison
    current_season = df['Show'].str.extract(r'(S\d+)')[0].dropna().max()
    df = df[df['Show'].str.contains(f'{current_season}E', na=False)]
    print(f"{len(df)} Matches geladen (nur {current_season})")
    
    stats, tag_stats = compute_stats(df)
    current = get_current_champions(df)
    ranking = compute_ranking(stats, current)
    tag_ranking = compute_tag_ranking(tag_stats)
    top = get_top_matches(df)
    history = get_championship_history(df)
    
    if ranking:
        print(f"#1: {ranking[0]['name']} ({ranking[0]['score']:.0f} pts)")
    if tag_ranking:
        print(f"#1 Tag: {tag_ranking[0]['name']} ({tag_ranking[0]['score']:.0f} pts)")
    
    md = generate_markdown(ranking, tag_ranking, current, top, history, df, current_season)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(md, encoding='utf-8')
    print(f"Saved: {OUTPUT_FILE} ({len(md):,} chars)")
    print("Done!")
    return True

if __name__ == '__main__':
    main()
