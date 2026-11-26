"""
Writes brief.pdf: the one-page Attorney & CPA Briefing Sheet (letter size).

Uses only the same rounded results and placeholders as brief.html (build_site.py).
Run after build_site.py:  python3 tools/build_brief_pdf.py
Requires ReportLab (pip install reportlab). Not needed by the site itself.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import build_site as B  # noqa: E402
import content as C  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

OUT = os.path.join(ROOT, "brief.pdf")

base = ParagraphStyle("b", fontName="Helvetica", fontSize=7.6, leading=9.2)
small = ParagraphStyle("s", parent=base, fontSize=6.6, leading=8, textColor=colors.HexColor("#4a5568"))
head = ParagraphStyle("h", parent=base, fontName="Helvetica-Bold", fontSize=8.4, leading=10, spaceBefore=3, spaceAfter=1)
title = ParagraphStyle("t", parent=base, fontName="Helvetica-Bold", fontSize=11, leading=13)


def P(text, style=base):
    return Paragraph(text, style)


def bullets(items, style=base):
    return [P("&bull; " + i, style) for i in items]


def source_cell(source_ids):
    """Clickable source IDs with their evidence status, using the shared register."""
    out = []
    for source_id in source_ids:
        source = C.SOURCES[source_id]
        url = source["url"].replace("&", "&amp;").replace('"', "&quot;")
        label = source_id.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        status = source["status"].replace("&", "&amp;")
        out.append(f'<link href="{url}">{label}</link> <font color="#4a5568">({status})</font>')
    return "<br/>".join(out) if out else "UNVERIFIED"


def build():
    facts = [
        ["Property A: value, Nov 2026", "held internally (household estimate; not an appraisal)", ["HOUSEHOLD"]],
        ["Property A: Prop 19 allowance", "$1,044,590 (BOE, secondary)", ["BOE-LTA-2025-009", "BOE-PROP19-INTRO"]],
        ["Property A: Prop 13 factor", "1.02 a year (BOE, secondary)", ["BOE-LTA-2026-002"]],
        ["Property B: unit/lease details", "held internally (not published)", ["HOUSEHOLD", "SF-RENT-BOARD"]],
        ["Federal exclusion, per person", "$15,000,000 (2026; IRS); $15,480,000 (2027; secondary)", ["IRS-IR-2025-103", "IRS-NEWS-2027"]],
        ["Local parcel-tax measure", "passed, preliminary; certification pending", ["SF-ELECTIONS-2026"]],
        ["Base: sell and invest (2045, 20 years)", B.money(B.BASE["S"]), ["MODEL", "IRS-PUB-523", "FTB-540ES-2025"]],
        ["Base: live with no rent credit", B.money(B.BASE["L"]), ["MODEL", "BOE-PROP19-INTRO", "IRS-PUB-523"]],
    ]
    rows = [[P("Topic", head), P("Value / status", head), P("Source links", head)]]
    rows += [[P(a, base), P(b, base), P(source_cell(source_ids), small)] for a, b, source_ids in facts]
    t = Table(rows, colWidths=[1.75 * inch, 2.8 * inch, 2.45 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf2f7")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    results = (
        f"Sell and invest {B.money(B.BASE['S'])}; phased over 24 months {B.money(B.BASE['SP24'])}; "
        f"rent then sell {B.money(B.BASE['R'])}; live with no rent credit {B.money(B.BASE['L'])}. "
        f"Living ties with selling only at a rent credit of about {B.pct(B.BE_CREDIT, 0)}. "
        "Provisional lean: sell in the transfer year. Not a decision. Real 2026 dollars, rounded to $10."
    )
    qa = ["Is the trust funded for Property A, and what is the date-of-death valuation plan?",
          "Is portability to be elected, and were prior taxable gifts made (Form 709)?",
          "Will the heir occupy Property A within one year; when is the homeowners' exemption filed?",
          "Who files the BOE-19-P claim, and when is it calendared?",
          "Counsel to confirm the Prop 19 reading after a move-out (reading A or B)."]
    qc = ["Basis at date of death and the transfer-year sale (step-up; section 121 if the heir lives there).",
          "Confirm the 1% Behavioral Health Services Tax and the state rate on large gains.",
          "Depreciation and recapture if Property A is rented; the land share is needed.",
          "Solar credit tariff (NEM 3.0 or earlier) and property tax on the Prop 19 base.",
          "Trust income tax: compressed brackets if sale income stays in the trust."]
    dl = ["Day 0: date of death; appraisal at date of death.",
          "9 months: Form 706 if required or to elect portability (6-month extension on Form 4768).",
          "Within 1 year: occupancy and homeowners' exemption (Prop 19 only).",
          "Within 3 years of transfer: BOE-19-P claim (secondary).",
          "Within 5 years: late portability relief (Rev. Proc. 2022-32; secondary)."]
    law = ["Enacted: federal $15,000,000 exclusion (2026); Prop 19 family-home rules; 1% state surcharge over $1,000,000.",
           "Proposed or reported, not enacted: federal estate-tax changes (not in the model).",
           "Secondary, to check: SF transfer-tax tiers (unverified); 2027 federal figures; SB 974."]
    flags = ["Property A market rent and insurance: unverified.",
             "Historical tax records: check against bills.",
             "Prop 19 move-out reading: counsel to confirm.",
             "Measure H tier for Property B: not verified."]
    story = [
        P("Attorney &amp; CPA Briefing Sheet", title),
        P(f"Property A (inherited) and Property B (already owned) &middot; prepared {C.CHECKED} &middot; placeholders for all names. Rounded outputs are not guaranteed anonymous; the public Git history has not been purged. Not legal or tax advice.", small),
        Spacer(1, 4),
        P("1. Key facts (household figures held internally)", head), t,
        P("2. Results", head), P(results),
        P("3. Deadlines", head), *bullets(dl),
        P("4. Questions for counsel", head), *bullets(qa),
        P("5. Questions for the CPA", head), *bullets(qc),
        P("6. Law status", head), *bullets(law),
        P("7. Flags", head), *bullets(flags),
        Spacer(1, 4),
        P("Sources: IRS IR-2025-103 and What's new (estate and gift tax); FTB Form 540-ES instructions; U.S. Treasury yield table; "
          "CBO Feb 2026 outlook; SF Department of Elections (Nov 3, 2026, preliminary). Full register: sources.html.", small),
    ]
    doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.45 * inch, bottomMargin=0.45 * inch,
                            title="Attorney and CPA Briefing Sheet", author="Inheritance decision dashboard")
    doc.build(story)
    pages = len(__import__("re").findall(rb"/Type\s*/Page[^s]", open(OUT, "rb").read()))
    print(f"wrote brief.pdf ({pages} page(s))")
    if pages != 1:
        raise SystemExit("brief.pdf must be one page; shorten the text.")


if __name__ == "__main__":
    build()
