"""
site_lib.py — layout and table primitives shared by the page builders in site_pages.py.

Everything is pre-rendered as HTML so the pages work with JavaScript off and print correctly;
the JS layer only adds sorting, the what-if controls and the charts.
Privacy: every dollar figure has passed r10() and the text scrubber in build.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The published site lives in its own directory so it cannot collide with the other site this
# repository also publishes (the root index.html belongs to an earlier session). Everything the
# builders write goes here: pages, stylesheet, scripts and the browser data file.
OUT = os.path.join(ROOT, "decision-workspace")
sys.path.insert(0, HERE)

from build import scrub_str  # noqa: E402
from inputs import (PROPERTY_A, PROPERTY_B, RULES, ECON, TRANSACT, PHASING, SOURCES,  # noqa: E402
                    QUESTIONS, SUGGESTIONS, FLAGS, HISTORY_A, HISTORY_B, r10)
import engine as E  # noqa: E402
import history as H  # noqa: E402
import projections as P  # noqa: E402
import registers as R  # noqa: E402

ASOF = "2026-11-25"
NEXT_CHECK = "2026-12-15"

PAGES = [
    ("Decide", [("index", "Overview"), ("paths", "Paths"), ("what-if", "What if"),
                ("framework", "Decision rules"), ("briefing", "Briefing sheet")]),
    ("Model", [("projections", "Projections"), ("tax-rules", "Tax rules"),
               ("costs", "Costs & capital"), ("process", "Process & deadlines"),
               ("model", "How it works")]),
    ("Risk", [("black-swan", "Black swans"), ("phased", "Phased investing"),
              ("watch", "Law watch"), ("recheck", "Annual recheck")]),
    ("Registers", [("open-questions", "Open questions"), ("suggestions", "Suggestions"),
                  ("flagged", "Flagged"), ("comparables", "Comparables"),
                  ("sources", "Sources"), ("glossary", "Glossary")]),
]


# ------------------------------------------------------------------ helpers ----
def e(x):
    return scrub_str(str(x)) if x is not None else ""


def m(v, dash="&mdash;"):
    """money cell: already rounded to $10 by the model; blank when unverified."""
    if v is None:
        return '<span class="na">not verified</span>'
    n = int(round(float(v) / 10.0) * 10)
    sign = "-" if n < 0 else ""
    return sign + "$" + format(abs(n), ",d")


def money0(v):
    return m(v)


def pc(v, dp=2, sign=False):
    if v is None:
        return '<span class="na">not verified</span>'
    s = "+" if (sign and v > 0) else ""
    return f"{s}{float(v) * 100:.{dp}f}%"


def num(v, dp=0):
    if v is None:
        return '<span class="na">not verified</span>'
    return f"{float(v):,.{dp}f}" if dp else format(int(v), ",d")


def srclink(key, extra=""):
    """Inner HTML for a Source column. `key` is a SOURCES id, 'owner', 'model', or None."""
    tail = f" <span class=\"small\">{extra}</span>" if extra else ""
    if not key:
        return '<span class="u">no source located</span>' + tail
    if key == "owner":
        return '<span class="u">owner-supplied &middot; unverified</span>' + tail
    if key == "model":
        return '<span class="u">computed here from the rows above</span>' + tail
    if key == "derived":
        return ('<span class="u">computed here</span> '
                '<a href="sources.html">from these inputs</a>' + tail)
    if key.startswith("@"):                      # a pointer to another page of this workspace
        return f'<a href="{key[1:]}.html">{key[1:].replace("-", " ")} page</a>' + tail
    srec = SOURCES.get(key)
    if not srec:
        return e(key) + tail
    status = srec[2]
    link_cls = "" if status.startswith("official") else ' class="u"'
    tag = {"official": "official", "official-ballot-summary": "ballot text",
           "academic": "academic", "owner": "owner"}.get(status, status)
    return (f'<a{link_cls} href="{e(srec[1])}" target="_blank" rel="noopener noreferrer" '
            f'title="{e(srec[0])}">{e(key)}</a> <span class="small">{tag}</span>' + tail)


def flagref(key):
    return '<a href="flagged.html" class="pill bad">flagged</a>'


_SRC = {"keys": ["derived"]}


def SRC(*keys):
    """Declare what the tables on this page rest on. Any table that does not build its own
    Source column gets one filled from here, so 'every row carries a source' is enforced by the
    renderer rather than remembered by the author."""
    _SRC["keys"] = list(keys)


def _auto_src_cell():
    parts = []
    for k in _SRC["keys"]:
        cell = srclink(k)
        parts.append(cell.replace('<td class="src">', "").replace("</td>", "")
                     if cell.startswith("<td") else cell)
    return " ".join(parts)


def simple_table(headers, rows, caption="", cls="", short=False):
    """headers: list of (label, align); rows: list of lists of pre-rendered cells.
    A trailing Source column is added automatically unless the caller already has one
    (a header whose align is 'src'), so no table can be published unsourced."""
    if not any(h[1] == "src" for h in headers) and headers:
        headers = list(headers) + [("Source", "src")]
        rows = [list(r) + [None] for r in rows]
        added = True
    else:
        added = False
    h = ['<div class="wrap' + (" short" if short else "") + '"><table class="' + cls + '">']
    if caption:
        h.append(f"<caption>{caption}</caption>")
    h.append("<thead><tr>")
    for lab, align in headers:
        hc = "num" if align == "r" else ("" if align == "l" else align)
        h.append(f'<th class="{hc}">{lab}</th>')
    h.append("</tr></thead><tbody>")
    for r in rows:
        rc = ""
        cells = list(r)
        if cells and isinstance(cells[0], str) and cells[0].startswith("@"):
            mark = cells[0][1:]
            rc = f' class="{mark}"' if mark else ""
            cells = cells[1:]
        h.append("<tr" + rc + ">")
        for i, (lab, align) in enumerate(headers):
            tc = "num" if align == "r" else ("" if align == "l" else align)
            if added and i == len(headers) - 1:
                cell = _auto_src_cell()
            else:
                cell = cells[i] if i < len(cells) else ""
            h.append(f'<td class="{tc}">{cell}</td>')
        h.append("</tr>")
    h.append("</tbody></table></div>")
    return "".join(h)


def pill(text, kind=""):
    return f'<span class="pill {kind}">{text}</span>'


STATUS_LABEL = {
    "enacted-verified": ("enacted &amp; read", "ok"),
    "enacted-not-read": ("enacted &middot; text not read", "info"),
    "pending-certification": ("passed &middot; awaiting certification", "warn"),
    "proposed": ("proposed &mdash; not law", "warn"),
    "unverified": ("unverified", "bad"),
    "official": ("official", "ok"),
    "official-ballot-summary": ("ballot text", "ok"),
    "academic": ("academic", "info"),
    "owner": ("owner-supplied", "warn"),
    "unverified-owner": ("owner-supplied", "warn"),
}


def status_pill(st):
    lab, kind = STATUS_LABEL.get(st, (st, ""))
    return pill(lab, kind)


def note(text):
    return f'<p class="small">{text}</p>'


def head(active, title, blurb="", body_class=""):
    nav = ['<header class="top"><a class="brand" href="index.html">'
           'Property A &amp; B &middot; decision workspace</a>'
           '<span class="sub">inherited Cupertino house &middot; owned SF triplex &middot; '
           "transfer modelled at 2045</span>"
           '<span class="privacy">Privacy mode: every figure rounded to $10 &middot; no names, '
           "addresses or parcel numbers &middot; no analytics, no cookies</span></header>",
           '<nav class="groups">']
    for grp, items in PAGES:
        nav.append(f'<div class="grp"><b>{grp}</b>')
        for pid, label in items:
            cur = ' aria-current="page"' if pid == active else ""
            nav.append(f'<a href="{pid}.html"{cur}>{label}</a>')
        nav.append("</div>")
    nav.append("</nav>")
    h1 = f"<h1>{title}</h1>"
    intro = f'<p class="lede">{blurb}</p>' if blurb else ""
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{title} &middot; Property A &amp; B decision workspace</title>"
            '<meta name="robots" content="noindex,nofollow">'
            '<link rel="stylesheet" href="assets/app.css"></head>'
            f'<body class="{body_class}" data-page="{active}">'
            + "".join(nav) + "<main>" + h1 + intro)


FOOT = ('<p class="footnote">Built as a decision workspace, not advice. Every figure on this site is '
        "rounded to the nearest $10 so it cannot be matched to a public record; exact values are only "
        "in the household's offline folder. Values with no official source are left blank and flagged "
        "rather than estimated. Rule data verified <b>" + ASOF + "</b>; next scheduled recheck <b>" +
        NEXT_CHECK + "</b>. <a href=\"sources.html\">Source register</a> &middot; "
        '<a href="flagged.html">Flagged for review</a> &middot; <a href="glossary.html">Glossary</a>.</p>')


def page(active, title, body, blurb=""):
    scripts = ('<script src="assets/data.js"></script>'
               '<script src="assets/app.js"></script>'
               '<script src="assets/pages.js"></script></body></html>')
    return head(active, title, blurb) + body + FOOT + "</main>" + scripts


def write(name, html):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(html)
    print(f"  {name:22s} {os.path.getsize(path)/1024:7.1f} KB")
