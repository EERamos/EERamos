"""Generate the SVG cards for the EERamos profile README.

Every card paints its own background (navy + amber, the palette of the live
dashboards) so it renders identically on GitHub's light and dark themes.
Only ``activity.svg`` depends on live GitHub data; everything else is static.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

USER = "EERamos"
OUT = Path("assets")
TOKEN = os.getenv("GITHUB_TOKEN", "")
TZ = ZoneInfo("America/Mexico_City")
NOW = dt.datetime.now(dt.timezone.utc)
SINCE = NOW - dt.timedelta(days=365)

# Palette lifted from bsm-calculator/index.html so profile and apps read as one system.
BG = "#0d1220"
RAISED = "#131a2c"
BORDER = "#232d4d"
TEXT = "#eaf0fb"
MUTED = "#a8b3d0"
FAINT = "#7884a8"
ACCENT = "#f0b400"
CALL = "#2dd4a7"
PUT = "#ff6d92"
HEADER_INK = "#7d88a6"  # readable on both white and dark page backgrounds
MONO = 'ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace'
W = 900

PROJECTS = [
    {
        "name": "bsm-calculator",
        "live": "https://eeramos.github.io/bsm-calculator/",
        "blurb": "European option prices and the full Greek set, redrawn live as you move the inputs.",
        "tags": "derivatives · Greeks · JavaScript",
        "preview": "bsm-calculator.png",
    },
    {
        "name": "bsm-risky-calibration",
        "live": "https://eeramos.github.io/bsm-risky-calibration/",
        "blurb": "Back out the volatility that absorbs a credit or funding spread, via Newton-Raphson.",
        "tags": "credit risk · calibration · JavaScript",
        "preview": "bsm-risky-calibration.png",
    },
    {
        "name": "sector-return-normality",
        "live": "https://eeramos.github.io/sector-return-normality/",
        "blurb": "All 11 S&P 500 sectors ranked by how closely daily returns follow a normal distribution.",
        "tags": "market statistics · time series · JavaScript",
        "preview": "sector-return-normality.png",
    },
]

# Hand-curated. Edit freely; the card lays chips out automatically.
TOOLKIT = [
    ("PRICING & RISK", ["Black-Scholes-Merton", "Greeks", "implied & risky vol",
                        "Newton-Raphson calibration", "credit spreads", "market risk"]),
    ("RESEARCH & STATS", ["return distributions", "normality tests", "sector analysis",
                          "Python", "NumPy / SciPy", "pandas"]),
    ("BUILD", ["JavaScript", "HTML / CSS", "GitHub Pages", "GitHub Actions", "generated SVG"]),
    ("APPLIED AI", ["agentic workflows", "Claude Code", "MCP", "knowledge systems", "automation"]),
]


# ---------------------------------------------------------------- helpers ---

def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def tw(text: str, size: float) -> float:
    """Approximate rendered width of monospace text."""
    return len(text) * size * 0.62


def svg_shell(height: int, body: str, width: int = W, card: bool = True) -> str:
    background = (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="16" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        if card else ""
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
  text {{ font-family: {MONO}; }}
  .t {{ fill: {TEXT}; }}
  .m {{ fill: {MUTED}; }}
  .f {{ fill: {FAINT}; }}
  .a {{ fill: {ACCENT}; }}
  .h {{ fill: {HEADER_INK}; }}
</style>
{background}
{body}
</svg>'''


def write(name: str, content: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")


def api_get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "EERamos-profile-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def github(path: str, params: dict | None = None):
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return api_get(url)


# ------------------------------------------------------------- quant bits ---

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_call(s: float, k: float, r: float, sigma: float, t: float) -> float:
    """Black-Scholes-Merton European call price (no dividends)."""
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return s * _norm_cdf(d1) - k * math.exp(-r * t) * _norm_cdf(d2)


# ------------------------------------------------------------ static cards ---

def section_header(title: str, subtitle: str = "") -> str:
    title_w = tw(title, 12) + len(title) * 1.6 + 16  # letter-spacing adds width
    parts = [
        f'<text class="h" x="0" y="20" font-size="12" letter-spacing="1.6">{esc(title)}</text>',
        f'<line x1="{title_w:.0f}" y1="15" x2="{W}" y2="15" stroke="{HEADER_INK}" stroke-opacity="0.35" stroke-width="1"/>',
    ]
    if subtitle:
        parts.append(f'<rect x="{W - tw(subtitle, 10) - 12:.0f}" y="8" width="{tw(subtitle, 10) + 12:.0f}" height="14" fill="transparent"/>')
        parts.append(f'<text class="h" x="{W}" y="20" font-size="10" text-anchor="end">{esc(subtitle)}</text>')
    return svg_shell(30, "\n".join(parts), card=False)


def hero_svg() -> str:
    """Name card with a call-price curve drawn from the real BSM formula."""
    x0, x1, y0, y1 = 560, 866, 44, 168  # plot box
    k, lo, hi = 100.0, 60.0, 140.0
    spots = [lo + i for i in range(int(hi - lo) + 1)]
    prices = [bsm_call(s, k, 0.03, 0.25, 1.0) for s in spots]
    intrinsic = [max(s - k, 0.0) for s in spots]
    vmax = max(prices)

    def pt(s: float, v: float) -> str:
        px = x0 + (s - lo) / (hi - lo) * (x1 - x0)
        py = y1 - v / vmax * (y1 - y0)
        return f"{px:.1f},{py:.1f}"

    curve = " ".join(pt(s, v) for s, v in zip(spots, prices))
    hockey = " ".join(pt(s, v) for s, v in zip(spots, intrinsic))
    kx = x0 + (k - lo) / (hi - lo) * (x1 - x0)
    body = f'''
<text class="a" x="36" y="46" font-size="11" letter-spacing="2.2">MARKETS · MODELS · AUTOMATION</text>
<text class="t" x="36" y="94" font-size="38" font-weight="700" letter-spacing="1">EDUARDO RAMOS</text>
<rect class="a" x="36" y="108" width="64" height="3" rx="1.5"/>
<text class="m" x="36" y="136" font-size="14">CFA charterholder · CQF candidate</text>
<text class="m" x="36" y="158" font-size="12">Derivatives &amp; quantitative finance by profession · applied AI by curiosity</text>
<text class="f" x="36" y="182" font-size="11">MSCI · Mexico City</text>

<polygon points="{pt(lo, 0)} {curve} {pt(hi, 0)}" fill="{ACCENT}" fill-opacity="0.08"/>
<polyline points="{hockey}" fill="none" stroke="{FAINT}" stroke-width="1" stroke-dasharray="3 4"/>
<polyline points="{curve}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linejoin="round"/>
<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{BORDER}" stroke-width="1"/>
<line x1="{kx:.1f}" y1="{y1}" x2="{kx:.1f}" y2="{y1 + 5}" stroke="{FAINT}" stroke-width="1"/>
<text class="f" x="{kx:.1f}" y="{y1 + 16}" font-size="9" text-anchor="middle">K</text>
<text class="a" x="{x0}" y="{y0 + 2}" font-size="10">C(S) · Black-Scholes-Merton</text>
<text class="f" x="{x0}" y="{y0 + 16}" font-size="9">dashed: max(S − K, 0)</text>
'''
    return svg_shell(210, body)


def focus_map_svg() -> str:
    cards = [
        (28, 34, "01", "DERIVATIVES", "pricing · Greeks · volatility"),
        (466, 34, "02", "RISK + CALIBRATION", "market risk · credit · model calibration"),
        (28, 146, "03", "SYSTEMATIC RESEARCH", "statistics · signals · testing"),
        (466, 146, "04", "APPLIED AI", "agents · workflows · knowledge systems"),
    ]
    cx, cy = 450, 130
    parts = [
        f'<line x1="{cx}" y1="34" x2="{cx}" y2="228" stroke="{ACCENT}" stroke-opacity="0.35"/>',
        f'<line x1="28" y1="{cy}" x2="872" y2="{cy}" stroke="{ACCENT}" stroke-opacity="0.35"/>',
        f'<circle cx="{cx}" cy="{cy}" r="42" fill="{RAISED}" stroke="{ACCENT}" stroke-width="1.5"/>',
        f'<text class="a" x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="13" font-weight="700">CFA</text>',
        f'<text class="a" x="{cx}" y="{cy + 15}" text-anchor="middle" font-size="13" font-weight="700">CQF</text>',
    ]
    for x, y, num, title, subtitle in cards:
        parts.extend([
            f'<rect x="{x}" y="{y}" width="406" height="82" rx="12" fill="{RAISED}" stroke="{BORDER}"/>',
            f'<text class="a" x="{x + 18}" y="{y + 26}" font-size="11" font-weight="700">{num}</text>',
            f'<text class="t" x="{x + 52}" y="{y + 31}" font-size="14" font-weight="700">{esc(title)}</text>',
            f'<text class="m" x="{x + 52}" y="{y + 55}" font-size="11">{esc(subtitle)}</text>',
        ])
    return svg_shell(262, "\n".join(parts))


def toolkit_svg() -> str:
    label_x, chips_x, max_x = 28, 200, W - 28
    size, pad, gap, row_h, group_gap = 11, 11, 8, 30, 14
    y = 24
    parts: list[str] = []
    for label, chips in TOOLKIT:
        parts.append(f'<text class="a" x="{label_x}" y="{y + 15}" font-size="10" letter-spacing="1.4">{esc(label)}</text>')
        x = chips_x
        for chip in chips:
            w = tw(chip, size) + 2 * pad
            if x + w > max_x:
                x = chips_x
                y += row_h
            parts.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="22" rx="11" fill="{RAISED}" stroke="{BORDER}"/>')
            parts.append(f'<text class="t" x="{x + w / 2:.1f}" y="{y + 15}" font-size="{size}" text-anchor="middle">{esc(chip)}</text>')
            x += w + gap
        y += row_h + group_gap
    return svg_shell(y + 4, "\n".join(parts))


# ------------------------------------------------------------ github data ---

def list_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = github(
            f"/users/{USER}/repos",
            {"type": "owner", "sort": "pushed", "direction": "desc", "per_page": 100, "page": page},
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repos if r.get("name") != USER and not r.get("fork")]


def repo_commits(repo_full_name: str) -> list[dict]:
    commits: list[dict] = []
    for page in range(1, 11):
        try:
            batch = github(
                f"/repos/{repo_full_name}/commits",
                {"author": USER, "since": SINCE.isoformat().replace("+00:00", "Z"), "per_page": 100, "page": page},
            )
        except Exception:
            break
        if not isinstance(batch, list) or not batch:
            break
        commits.extend(batch)
        if len(batch) < 100:
            break
    return commits


def collect_commit_dates(repos: list[dict]) -> list[dt.datetime]:
    dates: list[dt.datetime] = []
    for repo in repos:
        for item in repo_commits(repo["full_name"]):
            stamp = ((item.get("commit") or {}).get("author") or {}).get("date")
            if not stamp:
                continue
            try:
                dates.append(dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")))
            except ValueError:
                pass
    return dates


# ------------------------------------------------------------ dynamic card ---

def month_keys(now_local: dt.datetime) -> list[tuple[int, int]]:
    """Twelve (year, month) keys ending at ``now_local``'s month."""
    keys = []
    year, month = now_local.year, now_local.month
    for _ in range(12):
        keys.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return keys[::-1]


def activity_svg(dates: list[dt.datetime], now: dt.datetime | None = None) -> str:
    now_local = (now or NOW).astimezone(TZ)
    keys = month_keys(now_local)
    local = [d.astimezone(TZ) for d in dates]
    counts = Counter((d.year, d.month) for d in local)
    values = [counts[k] for k in keys]
    total = len(local)
    active_days = len({d.date() for d in local})
    best = max(values) if values else 0
    day_word = "active day" if active_days == 1 else "active days"

    chart_x, chart_y, chart_w, chart_h = 400, 40, 470, 80
    gap = 10
    bar_w = (chart_w - gap * 11) / 12
    bars = []
    for i, ((year, month), count) in enumerate(zip(keys, values)):
        x = chart_x + i * (bar_w + gap)
        height = 3 if best == 0 or count == 0 else max(3, chart_h * count / best)
        y = chart_y + chart_h - height
        fill = ACCENT if count else RAISED
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height:.1f}" rx="3" fill="{fill}" '
            f'data-month="{year}-{month:02d}" data-count="{count}"/>'
        )
        label = dt.date(year, month, 1).strftime("%b").lower()
        bars.append(f'<text class="f" x="{x + bar_w / 2:.1f}" y="{chart_y + chart_h + 18}" font-size="9" text-anchor="middle">{label}</text>')
        if count:
            bars.append(f'<text class="m" x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" font-size="9" text-anchor="middle">{count}</text>')

    body = f'''
<text class="f" x="28" y="36" font-size="10" letter-spacing="1.4">PUBLIC COMMITS · PAST 12 MONTHS</text>
<text class="a" x="28" y="88" font-size="44" font-weight="700">{total:,}</text>
<text class="m" x="28" y="114" font-size="11">{active_days} {day_word} · best month {best}</text>
<text class="f" x="28" y="136" font-size="9">original public repositories only · Mexico City time</text>
{''.join(bars)}
<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="{BORDER}"/>
'''
    return svg_shell(156, body)


# --------------------------------------------------------------- pipeline ---

def write_static() -> None:
    write("hero.svg", hero_svg())
    write("h-work.svg", section_header("SELECTED WORK", "three live dashboards · click to open"))
    write("h-focus.svg", section_header("FOCUS", "CQF · financial engineering · applied AI"))
    write("h-toolkit.svg", section_header("TOOLKIT", "what the work is built with"))
    write("h-activity.svg", section_header("PUBLIC BUILD ACTIVITY", "generated from public GitHub data"))
    write("h-elsewhere.svg", section_header("ELSEWHERE", "connect"))
    write("focus-map.svg", focus_map_svg())
    write("toolkit.svg", toolkit_svg())


def main() -> None:
    write_static()
    try:
        repos = list_repos()
        dates = collect_commit_dates(repos)
        write("activity.svg", activity_svg(dates))
    except Exception as exc:  # keep the last good card if the API is unavailable
        if not (OUT / "activity.svg").exists():
            message = esc(f"Activity refresh unavailable: {type(exc).__name__}")
            write("activity.svg", svg_shell(90, f'<text class="m" x="24" y="52" font-size="12">{message}</text>'))


if __name__ == "__main__":
    main()
