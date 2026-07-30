---
permalink: /index.html
layout: layouts/index.njk
title: "Choke Slam Wrestling"
---

<style>
/* ═══════════════ CSW DRAMATIC HOMEPAGE ═══════════════ */
:root{--gold:#f59e0b;--gold-bright:#fbbf24;--purple:#7c3aed;--dark:#0a0a0f;--card:#1a1025;--red:#ef4444;--green:#22c55e;--blue:#3b82f6}

*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--dark);color:#f0e6ff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow-x:hidden}

/* ── Hero ── */
.hero{position:relative;min-height:85vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;overflow:hidden;background:radial-gradient(ellipse at center,#1a0a30 0%,#0a0a0f 70%)}
.hero::before{content:'';position:absolute;inset:0;background:url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="none" stroke="%234b0082" stroke-width="0.3" opacity="0.3"/><line x1="0" y1="33" x2="100" y2="33" stroke="%234b0082" stroke-width="0.2" opacity="0.2"/><line x1="0" y1="66" x2="100" y2="66" stroke="%234b0082" stroke-width="0.2" opacity="0.2"/></svg>');opacity:0.4;animation:drift 20s linear infinite}
@keyframes drift{0%{transform:translateY(0)}100%{transform:translateY(-100px)}}

/* Pyro particles */
.particles{position:absolute;inset:0;pointer-events:none}
.particle{position:absolute;width:3px;height:3px;background:var(--gold);border-radius:50%;animation:rise 3s ease-out infinite;opacity:0}
@keyframes rise{0%{transform:translateY(100vh) scale(0);opacity:1}50%{opacity:0.8}100%{transform:translateY(-10vh) scale(2);opacity:0}}

/* Spotlight */
.spotlight{position:absolute;top:-20%;left:50%;transform:translateX(-50%);width:600px;height:120vh;background:radial-gradient(ellipse at top,rgba(245,158,11,0.08) 0%,transparent 70%);pointer-events:none;animation:pulse 4s ease-in-out infinite}
.spotlight2{left:20%;animation-delay:2s;opacity:0.5}
.spotlight3{left:80%;animation-delay:4s;opacity:0.3}
@keyframes pulse{0%,100%{opacity:0.3}50%{opacity:0.7}}

.hero-content{position:relative;z-index:1;padding:2rem}
.hero-logo{width:180px;filter:drop-shadow(0 0 30px rgba(245,158,11,0.5));animation:float 3s ease-in-out infinite;margin-bottom:1.5rem}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}

.hero h1{font-family:Georgia,serif;font-size:clamp(2rem,6vw,4rem);background:linear-gradient(180deg,var(--gold-bright) 0%,var(--gold) 50%,#b45309 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.5rem;letter-spacing:3px;text-shadow:none}
.hero .tagline{color:var(--purple);font-size:1.1rem;letter-spacing:4px;margin-bottom:2rem;animation:fadeIn 2s ease-out}
.hero .s08-badge{display:inline-block;background:linear-gradient(135deg,var(--gold),#d97706);color:var(--dark);font-weight:bold;padding:0.5rem 1.5rem;border-radius:30px;font-size:1.1rem;margin-bottom:2rem;animation:glow 2s ease-in-out infinite}
@keyframes glow{0%,100%{box-shadow:0 0 20px rgba(245,158,11,0.3)}50%{box-shadow:0 0 40px rgba(245,158,11,0.6)}}
@keyframes fadeIn{0%{opacity:0;transform:translateY(20px)}100%{opacity:1;transform:translateY(0)}}

/* ── Faction Showcase ── */
.factions{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;max-width:1000px;margin:3rem auto;padding:0 1rem}
.faction-card{background:var(--card);border-radius:16px;padding:2rem 1.5rem;text-align:center;position:relative;overflow:hidden;transition:transform 0.3s,box-shadow 0.3s;cursor:pointer;border:1px solid #2a1540}
.faction-card:hover{transform:translateY(-8px);box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.faction-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.faction-card.mm::before{background:linear-gradient(90deg,var(--red),#991b1b)}.faction-card.mm:hover{border-color:var(--red)}
.faction-card.srr::before{background:linear-gradient(90deg,var(--green),#166534)}.faction-card.srr:hover{border-color:var(--green)}
.faction-card.sns::before{background:linear-gradient(90deg,var(--blue),#1e40af)}.faction-card.sns:hover{border-color:var(--blue)}
.faction-emoji{font-size:3rem;margin-bottom:0.5rem;display:block}
.faction-card h3{font-size:1.3rem;margin-bottom:0.3rem}
.faction-card .manager{color:#9ca3af;font-size:0.85rem;margin-bottom:1rem}
.faction-card .stars{color:var(--gold);font-size:0.85rem;line-height:1.6}

/* ── Champion Banner ── */
.champion-strip{background:linear-gradient(90deg,#1a0a30,var(--card),#1a0a30);border-top:2px solid var(--gold);border-bottom:2px solid var(--gold);padding:2rem 1rem;text-align:center;margin:3rem 0}
.champion-strip h2{font-family:Georgia,serif;color:var(--gold);margin-bottom:1.5rem;font-size:1.5rem}
.champ-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;max-width:900px;margin:0 auto}
.champ-card{background:var(--dark);border:1px solid var(--gold);border-radius:10px;padding:1rem;transition:transform 0.2s}
.champ-card:hover{transform:scale(1.05);box-shadow:0 0 25px rgba(245,158,11,0.2)}
.champ-card .belt{font-size:2rem;margin-bottom:0.3rem}
.champ-card .title{font-size:0.7rem;color:var(--gold);text-transform:uppercase;letter-spacing:1px}
.champ-card .name{font-size:1rem;font-weight:bold;color:#f0e6ff}

/* ── Quick Links ── */
.quick-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;max-width:900px;margin:3rem auto;padding:0 1rem}
.quick-link{background:var(--card);border:1px solid #2a1540;border-radius:12px;padding:1.5rem;text-align:center;text-decoration:none;color:var(--purple);transition:all 0.3s;display:block}
.quick-link:hover{transform:translateY(-3px);border-color:var(--gold);background:#2a1540}
.quick-link .icon{font-size:2rem;display:block;margin-bottom:0.5rem}
.quick-link .label{font-size:0.9rem;font-weight:bold}

/* ── Scroll Indicator ── */
.scroll-down{position:absolute;bottom:2rem;left:50%;transform:translateX(-50%);animation:bounce 2s infinite}
.scroll-down span{display:block;width:30px;height:30px;border-right:2px solid var(--gold);border-bottom:2px solid var(--gold);transform:rotate(45deg)}
@keyframes bounce{0%,100%{opacity:0.3;transform:translateX(-50%) translateY(0)}50%{opacity:1;transform:translateX(-50%) translateY(10px)}}

/* ── Responsive ── */
@media(max-width:768px){.factions{grid-template-columns:1fr}.hero h1{font-size:2rem}.champ-grid{grid-template-columns:repeat(2,1fr)}}

/* ── Nav Override for Homepage ── */
.home-nav{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(10,10,15,0.9);backdrop-filter:blur(10px);border-bottom:1px solid #2a1540;padding:0.6rem 1rem;display:flex;justify-content:center;gap:0.3rem;flex-wrap:wrap}
.home-nav a{color:#9ca3af;text-decoration:none;padding:0.4rem 0.8rem;border-radius:6px;font-size:0.85rem;transition:all 0.2s}
.home-nav a:hover,.home-nav a.active{color:var(--gold);background:var(--card)}
</style>

<!-- Navigation -->
<nav class="home-nav">
  <a href="/choke-slam-wrestling/home/">🏠 Home</a>
  <a href="/choke-slam-wrestling/events/">📅 Events</a>
  <a href="/choke-slam-wrestling/wrestler/">🤼 Roster</a>
  <a href="/choke-slam-wrestling/championships/">🏆 Titles</a>
  <a href="/choke-slam-wrestling/statistiken/">📊 Stats</a>
  <a href="/choke-slam-wrestling/s08/" style="color:#f59e0b;">⚡ S08</a>
</nav>

<!-- Hero -->
<div class="hero">
  <div class="spotlight spotlight1"></div>
  <div class="spotlight spotlight2"></div>
  <div class="spotlight spotlight3"></div>
  <div class="particles" id="particles"></div>
  
  <div class="hero-content">
    <img src="https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/ChokeSlam_Hero_Banner.png" alt="Choke Slam Wrestling" style="max-width:90%;height:auto;border-radius:8px;margin-bottom:1.5rem;">
    <div class="s08-badge">⚡ SEASON 8 — COMING SOON ⚡</div>
  </div>
  
  <div class="scroll-down"><span></span></div>
</div>

<!-- Champions -->
<div class="champion-strip">
  <h2>🏆 CURRENT CHAMPIONS</h2>
  <div class="champ-grid">
    <div class="champ-card">
      <div class="belt">🌍</div>
      <div class="title">World Champion</div>
      <div class="name">Steve Austin</div>
    </div>
    <div class="champ-card">
      <div class="belt">🌏</div>
      <div class="title">International</div>
      <div class="name">Hiroshi Tanahashi</div>
    </div>
    <div class="champ-card">
      <div class="belt">👥</div>
      <div class="title">Tag Team</div>
      <div class="name">Bigelow & ZSJ</div>
    </div>
    <div class="champ-card">
      <div class="belt">👩</div>
      <div class="title">Womens</div>
      <div class="name">Sasha Banks</div>
    </div>
    <div class="champ-card">
      <div class="belt">👪</div>
      <div class="title">Trios</div>
      <div class="name">Hart·Bryan·Owen</div>
    </div>
  </div>
</div>

<!-- Factions -->
<div class="factions">
  <div class="faction-card mm" onclick="location.href='/choke-slam-wrestling/s08/'">
    <span class="faction-emoji">🛡️</span>
    <h3 style="color:#ef4444">Militanter Mummenschanz</h3>
    <p class="manager">Manager: Philipp Brunkovic</p>
    <p class="stars">⭐ AJ Styles · Chris Jericho · Shawn Michaels<br>Bret Hart · Daniel Bryan · Owen Hart</p>
  </div>
  <div class="faction-card srr" onclick="location.href='/choke-slam-wrestling/s08/'">
    <span class="faction-emoji">⚔️</span>
    <h3 style="color:#22c55e">Saint Rebel Radicalz</h3>
    <p class="manager">Manager: Pascal LePas</p>
    <p class="stars">⭐ Edge · Roman Reigns · Jay White<br>Jon Moxley · Bam Bam · ZSJ</p>
  </div>
  <div class="faction-card sns" onclick="location.href='/choke-slam-wrestling/s08/'">
    <span class="faction-emoji">🍸</span>
    <h3 style="color:#3b82f6">Sweet 'n Sour Elite</h3>
    <p class="manager">Manager: Hendrique Delafuente</p>
    <p class="stars">⭐ Okada · Tanahashi · Sasha Banks<br>Lady Apache · Akira Taue · Kamille</p>
  </div>
</div>

<!-- Quick Links -->
<div class="quick-links">
  <a href="/choke-slam-wrestling/events/" class="quick-link">
    <span class="icon">📅</span>
    <span class="label">Events</span>
  </a>
  <a href="/choke-slam-wrestling/wrestler/" class="quick-link">
    <span class="icon">🤼</span>
    <span class="label">Roster</span>
  </a>
  <a href="/choke-slam-wrestling/championships/" class="quick-link">
    <span class="icon">🏆</span>
    <span class="label">Championships</span>
  </a>
  <a href="/choke-slam-wrestling/statistiken/" class="quick-link">
    <span class="icon">📊</span>
    <span class="label">Statistics</span>
  </a>
</div>

<footer style="text-align:center;padding:3rem 1rem;color:#6b7280;font-size:0.85rem;border-top:1px solid #1f1530;margin-top:3rem">
  <p style="margin-bottom:0.5rem">🛡️ MM &nbsp; ⚔️ SRR &nbsp; 🍸 SnS</p>
  <p>© 2026 Choke Slam Wrestling — Season 8</p>
</footer>

<script>
// Generate floating particles
(function(){
  var container = document.getElementById('particles');
  for(var i=0;i<40;i++){
    var p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random()*100+'%';
    p.style.animationDelay = Math.random()*5+'s';
    p.style.animationDuration = (3+Math.random()*4)+'s';
    p.style.width = (2+Math.random()*4)+'px';
    p.style.height = p.style.width;
    container.appendChild(p);
  }
})();
</script>
