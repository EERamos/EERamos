from __future__ import annotations

import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_profile as gp  # noqa: E402

SVG_NS = {"s": "http://www.w3.org/2000/svg"}


def parse(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def test_bsm_call_matches_textbook_value():
    # S=100, K=100, r=5%, sigma=20%, T=1y -> 10.4506
    assert abs(gp.bsm_call(100, 100, 0.05, 0.20, 1.0) - 10.4506) < 1e-3


def test_hero_is_valid_svg_and_names_the_owner():
    svg = gp.hero_svg()
    parse(svg)
    assert "EDUARDO RAMOS" in svg
    assert "CFA" in svg and "CQF" in svg
    assert gp.BG in svg  # paints its own background


def test_section_header_is_valid_and_transparent():
    svg = gp.section_header("SELECTED WORK", "three live dashboards")
    root = parse(svg)
    assert "SELECTED WORK" in svg and "three live dashboards" in svg
    assert gp.BG not in svg  # headers sit on the page background
    assert root.get("width") == str(gp.W)


def test_focus_map_has_four_quadrants_and_center_badge():
    svg = gp.focus_map_svg()
    parse(svg)
    for label in ("DERIVATIVES", "RISK + CALIBRATION", "SYSTEMATIC RESEARCH", "APPLIED AI"):
        assert label in svg
    assert "CFA" in svg and "CQF" in svg


def test_toolkit_chips_stay_inside_the_card():
    svg = gp.toolkit_svg()
    root = parse(svg)
    rects = root.findall(".//s:rect", SVG_NS)
    assert len(rects) >= sum(len(chips) for _, chips in gp.TOOLKIT) + 1  # chips + background
    for rect in rects:
        assert float(rect.get("x")) + float(rect.get("width")) <= gp.W
    for label, chips in gp.TOOLKIT:
        assert gp.esc(label) in svg
        for chip in chips:
            assert gp.esc(chip) in svg


def test_write_static_emits_every_static_card_as_valid_xml(tmp_path, monkeypatch):
    monkeypatch.setattr(gp, "OUT", tmp_path)
    gp.write_static()
    names = {p.name for p in tmp_path.glob("*.svg")}
    expected = {"hero.svg", "focus-map.svg", "toolkit.svg", "h-work.svg", "h-focus.svg",
                "h-toolkit.svg", "h-activity.svg", "h-elsewhere.svg"}
    assert expected <= names
    for path in tmp_path.glob("*.svg"):
        parse(path.read_text(encoding="utf-8"))


def test_month_keys_returns_twelve_months_ending_now():
    now = dt.datetime(2026, 9, 9, 12, 0, tzinfo=gp.TZ)
    keys = gp.month_keys(now)
    assert len(keys) == 12
    assert keys[0] == (2025, 10)
    assert keys[-1] == (2026, 9)


def test_month_keys_wraps_across_january():
    keys = gp.month_keys(dt.datetime(2026, 2, 1, tzinfo=gp.TZ))
    assert keys[0] == (2025, 3) and keys[-1] == (2026, 2)


def test_activity_svg_with_no_commits_is_valid_and_shows_zero():
    svg = gp.activity_svg([], now=dt.datetime(2026, 9, 9, tzinfo=dt.timezone.utc))
    parse(svg)
    assert ">0<" in svg
    assert "0 active days" in svg


def test_activity_svg_buckets_by_mexico_city_month():
    # 2026-09-01 03:00 UTC is still Aug 31 in Mexico City (UTC-6).
    commit = dt.datetime(2026, 9, 1, 3, 0, tzinfo=dt.timezone.utc)
    svg = gp.activity_svg([commit], now=dt.datetime(2026, 9, 9, tzinfo=dt.timezone.utc))
    parse(svg)
    assert ">1<" in svg
    assert "1 active day" in svg
    assert 'data-month="2026-08" data-count="1"' in svg
    assert 'data-month="2026-09" data-count="0"' in svg
