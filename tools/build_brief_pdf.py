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


def build():
    facts = [
        ["Property A (Santa Clara County): value, Nov 2026", "held internally (household estimate; not an appraisal)"],
        ["Property A: Prop 19 allowance", "$1,044,590 (BOE, fetched; rounded)"],
        ["Property A: Prop 13 factor", "1.02 for 2026-27 (BOE, fetched)"],
        ["Property A: TRA/published tax rate", "blank (UNVERIFIED; private parcel lookup needed)"],
        ["Santa Clara county sale charges", "$0.55 per $500 DTT; $25 first recording page + $3/page after"],
        ["Property B (San Francisco): units", "three livable units; two rented; owner occupancy possible"],
        ["Federal exclusion, per person", "$15,000,000 (2026; IRS); $15,480,000 (2027; IRS)"],
        ["California state/local estate or inheritance tax", "No death-triggered tax; no California estate return for deaths since 2005"],
        ["Measure H (SF parcel tax)", "passed, preliminary, 74.42% yes; certification due by Dec 3, 2026"],
        ["Base: sell and invest (2045, 20 years)", B.money(B.BASE["S"])],
        ["Base: live with no rent credit", B.money(B.BASE["L"])],
    ]
    rows = [[P(a, base), P(b, base)] for a, b in facts]
    t = Table(rows, colWidths=[2.45 * inch, 4.55 * inch])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#edf2f7")),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    results = (
        f"Sell and invest {B.money(B.BASE['S'])} (simulated 10th-90th {B.money(B.MC['S']['p10'])} to {B.money(B.MC['S']['p90'])}); "
        f"phased 24 months {B.money(B.BASE['SP24'])} (simulated 10th-90th {B.money(B.MC['SP24']['p10'])} to {B.money(B.MC['SP24']['p90'])}); "
        f"rent then sell {B.money(B.BASE['R'])}; live with no rent credit {B.money(B.BASE['L'])}. "
        f"Living ties with selling only at a rent credit of about {B.pct(B.BE_CREDIT, 0)}. "
        "Provisional model lean: sell in transfer year. Not a household decision. Real 2026 dollars, rounded to $10."
    )
    qa = ["Is the trust funded for Property A, and what is the date-of-death valuation plan?",
          "Is portability to be elected, and were prior taxable gifts made (Form 709)?",
          "Will the heir occupy Property A within one year; when is the homeowners' exemption filed?",
          "Who files the BOE-19-P claim, and when is it calendared?",
          "Counsel to confirm the BOE Prop 19 move-out rule for the trust and title facts."]
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
    law = ["Enacted/current: federal exclusions (2026/2027); California has no death-triggered state/local tax under RTC 13301; Prop 19 family-home rules; 1% state surcharge only above $1,000,000 resident taxable income.",
           "Proposed or reported, not enacted: federal estate-tax changes (not in the model).",
           "Official sources checked: IRS 2027 release, BOE 2025 Prop 19 allowance/move-out guidance, BOE 2026-27 factor, FTB 2025 Form 540."]
    flags = ["Property A market rent, published TRA rate and insurance: unverified.",
             "Historical tax records and debt/payoff: check privately.",
             "Future Prop 19 allowance is unknown; model uses a labeled 2% proxy.",
             "Measure H tier for Property B: not verified.",
             "Income tax results simplified; CPA must apply filing status and other income."]
    story = [
        P("Attorney &amp; CPA Briefing Sheet", title),
        P(f"Property A (Santa Clara County, inherited) and Property B (San Francisco, owned) &middot; prepared {C.CHECKED} &middot; placeholders for all names. Not legal or tax advice.", small),
        Spacer(1, 4),
        P("1. Key facts (household figures held internally)", head), t,
        P("2. Results", head), P(results),
        P("3. Deadlines", head), *bullets(dl),
        P("4. Questions for counsel", head), *bullets(qa),
        P("5. Questions for the CPA", head), *bullets(qc),
        P("6. Law status", head), *bullets(law),
        P("7. Flags", head), *bullets(flags),
        Spacer(1, 4),
        P("Sources: IRS IR-2026-133 and Rev. Proc. 2026-35; BOE LTA 2025/009 and 2025/015, LTA 2026/002; CA RTC 13301; FTB 2025 Form 540; "
          "Santa Clara Clerk-Recorder; U.S. Treasury; CBO 2026 outlook; SF Department of Elections. Full register: sources.html.", small),
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
