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
