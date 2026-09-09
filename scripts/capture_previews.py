"""Screenshot the live dashboards into assets/previews/ (run locally, commit the PNGs).

Usage: python scripts/capture_previews.py
Needs Google Chrome or Microsoft Edge installed; no Python dependencies.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_profile import PROJECTS  # noqa: E402

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "chromium-browser",
]
OUT = Path("assets/previews")


def find_browser() -> str:
    for candidate in CANDIDATES:
        if Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    raise SystemExit("No Chrome/Edge found; install one or add its path to CANDIDATES.")


def capture(browser: str, url: str, target: Path) -> None:
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1200,750",
            "--virtual-time-budget=5000",
            f"--screenshot={target.resolve()}",
            url,
        ],
        check=True,
        timeout=120,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    browser = find_browser()
    OUT.mkdir(parents=True, exist_ok=True)
    for project in PROJECTS:
        target = OUT / project["preview"]
        capture(browser, project["live"], target)
        print(f"{target} ({target.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
