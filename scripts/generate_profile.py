from __future__ import annotations

import datetime as dt
import html
import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

USER = "EERamos"
OUT = Path("assets")
OUT.mkdir(exist_ok=True)
TOKEN = os.getenv("GITHUB_TOKEN", "")
ACCENT = "#0969da"
MUTED = "#656d76"
LIGHT_TEXT = "#24292f"
DARK_TEXT = "#f0f6fc"
LIGHT_FAINT = "#d0d7de"
DARK_FAINT = "#30363d"
TZ = ZoneInfo("America/Mexico_City")
NOW = dt.datetime.now(dt.timezone.utc)
SINCE = NOW - dt.timedelta(days=365)


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


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def svg_shell(width: int, height: int, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<style>
  .text {{ fill: {LIGHT_TEXT}; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }}
  .muted {{ fill: {MUTED}; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }}
  .accent {{ fill: {ACCENT}; }}
  .line {{ stroke: {LIGHT_FAINT}; }}
  @media (prefers-color-scheme: dark) {{
    .text {{ fill: {DARK_TEXT}; }}
    .muted {{ fill: #8c959f; }}
    .line {{ stroke: {DARK_FAINT}; }}
  }}
</style>
{body}
</svg>'''


def write(name: str, content: str):
    (OUT / name).write_text(content, encoding="utf-8")


def section_header(title: str, subtitle: str = "") -> str:
    body = [
        f'<text class="muted" x="0" y="22" font-size="13" letter-spacing="1.4">{esc(title)}</text>',
        '<line class="line" x1="155" y1="17" x2="900" y2="17" stroke-width="1"/>',
    ]
    if subtitle:
        body.append(f'<text class="muted" x="900" y="22" font-size="11" text-anchor="end">{esc(subtitle)}</text>')
    return svg_shell(900, 34, "\n".join(body))


def generate_static():
    greeting = svg_shell(
        900,
        170,
        f'''
<text class="muted" x="450" y="32" text-anchor="middle" font-size="12" letter-spacing="2">MARKETS · MODELS · AUTOMATION</text>
<text class="text" x="450" y="86" text-anchor="middle" font-size="38" font-weight="700" letter-spacing="1">EDUARDO RAMOS</text>
<rect class="accent" x="300" y="108" width="300" height="3" rx="1.5"/>
<text class="muted" x="450" y="142" text-anchor="middle" font-size="15">CFA charterholder · CQF candidate · quantitative finance + applied AI</text>
''',
    )
    write("greeting.svg", greeting)
    write("h-focus.svg", section_header("CURRENT FOCUS", "CQF · FINANCIAL ENGINEERING · APPLIED AI"))
    write("h-activity.svg", section_header("PUBLIC BUILD ACTIVITY", "generated from public GitHub data"))
    write("h-elsewhere.svg", section_header("ELSEWHERE", "connect"))


def list_repos():
    repos = []
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
    return [r for r in repos if not r.get("fork") and r.get("name") != USER]


def repo_commits(repo_full_name: str):
    commits = []
    for page in range(1, 11):
        try:
            batch = github(
                f"/repos/{repo_full_name}/commits",
                {
                    "author": USER,
                    "since": SINCE.isoformat().replace("+00:00", "Z"),
                    "per_page": 100,
                    "page": page,
                },
            )
        except Exception:
            break
        if not isinstance(batch, list) or not batch:
            break
        commits.extend(batch)
        if len(batch) < 100:
            break
    return commits


def collect_commit_dates(repos):
    dates = []
    for repo in repos:
        for item in repo_commits(repo["full_name"]):
            stamp = (((item.get("commit") or {}).get("author") or {}).get("date"))
            if not stamp:
                continue
            try:
                dates.append(dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")))
            except ValueError:
                pass
    return dates


def activity_svg(dates):
    start_day = SINCE.date()
    weeks = [0] * 53
    active_days = Counter()
    for d in dates:
        index = min(52, max(0, (d.date() - start_day).days // 7))
        weeks[index] += 1
        active_days[d.date()] += 1

    max_week = max(weeks) if weeks else 0
    chart_x, chart_y, chart_w, chart_h = 350, 50, 520, 92
    gap = 3
    bar_w = (chart_w - gap * (len(weeks) - 1)) / max(1, len(weeks))
    bars = []
    for i, count in enumerate(weeks):
        height = 2 if max_week == 0 else max(2, chart_h * count / max_week)
        x = chart_x + i * (bar_w + gap)
        y = chart_y + chart_h - height
        bars.append(f'<rect class="accent" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height:.1f}" rx="1" opacity="0.88"/>')

    body = f'''
<text class="muted" x="18" y="30" font-size="12">public commits, past year</text>
<text class="text" x="18" y="82" font-size="44" font-weight="700">{len(dates):,}</text>
<text class="muted" x="18" y="110" font-size="12">{len(active_days)} active days · best week {max_week}</text>
<text class="muted" x="350" y="30" font-size="12">commits per week</text>
{''.join(bars)}
<line class="line" x1="350" y1="146" x2="870" y2="146"/>
<text class="muted" x="350" y="166" font-size="10">12 months ago</text>
<text class="muted" x="870" y="166" font-size="10" text-anchor="end">now</text>
'''
    return svg_shell(900, 180, body)


def punch_svg(dates):
    hours = [0] * 24
    for d in dates:
        hours[d.astimezone(TZ).hour] += 1
    peak = max(hours) if hours else 0
    chart_x, chart_y, chart_w, chart_h = 38, 50, 824, 96
    gap = 5
    bar_w = (chart_w - gap * 23) / 24
    bars = []
    for h, count in enumerate(hours):
        height = 2 if peak == 0 else max(2, chart_h * count / peak)
        x = chart_x + h * (bar_w + gap)
        y = chart_y + chart_h - height
        bars.append(f'<rect class="accent" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height:.1f}" rx="1" opacity="0.88"/>')
    labels = []
    for h in (0, 3, 6, 9, 12, 15, 18, 21, 23):
        x = chart_x + h * (bar_w + gap) + bar_w / 2
        labels.append(f'<text class="muted" x="{x:.1f}" y="166" font-size="9" text-anchor="middle">{h:02d}</text>')
    body = f'''
<text class="muted" x="18" y="25" font-size="12">when I build · public commits by hour · Mexico City time</text>
<text class="muted" x="880" y="25" font-size="11" text-anchor="end">peak hour {peak} commits</text>
{''.join(bars)}
<line class="line" x1="38" y1="150" x2="862" y2="150"/>
{''.join(labels)}
'''
    return svg_shell(900, 180, body)


def recent_svg(repos):
    chosen = repos[:3]
    rows = []
    y = 42
    for repo in chosen:
        name = esc(repo.get("name"))
        desc = esc((repo.get("description") or "No description yet")[:88])
        language = esc(repo.get("language") or "—")
        pushed = (repo.get("pushed_at") or "")[:10]
        rows.append(f'<text class="text" x="18" y="{y}" font-size="14" font-weight="700">{name}</text>')
        rows.append(f'<text class="muted" x="18" y="{y+22}" font-size="11">{desc}</text>')
        rows.append(f'<text class="muted" x="880" y="{y}" font-size="11" text-anchor="end">{language} · {pushed}</text>')
        y += 62
    if not chosen:
        rows.append('<text class="muted" x="18" y="55" font-size="12">No public repositories yet.</text>')
    body = '<text class="muted" x="18" y="20" font-size="12">recently updated</text>\n' + "\n".join(rows)
    return svg_shell(900, 220, body)


def language_svg(repos):
    bytes_by_language = Counter()
    repo_count = Counter()
    for repo in repos:
        try:
            data = api_get(repo["languages_url"])
        except Exception:
            data = {}
        for lang, size in data.items():
            bytes_by_language[lang] += int(size)
            repo_count[lang] += 1

    top_bytes = bytes_by_language.most_common(5)
    top_repos = repo_count.most_common(5)

    def block(items, x, title, value_kind):
        total = sum(v for _, v in items) or 1
        max_v = max((v for _, v in items), default=1)
        out = [f'<text class="muted" x="{x}" y="24" font-size="12">{esc(title)}</text>']
        y = 52
        for name, value in items:
            out.append(f'<text class="text" x="{x}" y="{y}" font-size="11">{esc(name)}</text>')
            bar_x = x + 112
            width = 190 * value / max_v
            out.append(f'<rect class="accent" x="{bar_x}" y="{y-10}" width="{width:.1f}" height="9" rx="2" opacity="0.88"/>')
            label = f"{100*value/total:.0f}%" if value_kind == "share" else str(value)
            out.append(f'<text class="muted" x="{x+330}" y="{y}" font-size="10" text-anchor="end">{label}</text>')
            y += 28
        return "\n".join(out)

    body = block(top_bytes, 18, "top languages · by bytes", "share") + "\n" + block(top_repos, 470, "by repository count", "count")
    return svg_shell(900, 205, body)


def main():
    generate_static()
    try:
        repos = list_repos()
        dates = collect_commit_dates(repos)
        write("stats-activity.svg", activity_svg(dates))
        write("stats-punch.svg", punch_svg(dates))
        write("stats-recent.svg", recent_svg(repos))
        write("stats-langs.svg", language_svg(repos))
    except Exception as exc:
        message = esc(f"Profile refresh unavailable: {type(exc).__name__}")
        fallback = svg_shell(900, 90, f'<text class="muted" x="18" y="48" font-size="12">{message}</text>')
        for name in ("stats-activity.svg", "stats-punch.svg", "stats-recent.svg", "stats-langs.svg"):
            if not (OUT / name).exists():
                write(name, fallback)


if __name__ == "__main__":
    main()
