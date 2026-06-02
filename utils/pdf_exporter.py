"""
PDF Report Exporter — generates a professional stock analysis PDF report.
Uses fpdf2 with built-in Helvetica (Latin-1 safe).
All Unicode special chars are sanitised before writing.
"""
import os
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


# ── Unicode → Latin-1 sanitiser ───────────────────────────────────────────────
_REPLACEMENTS = {
    "\u2014": "-",    # em dash  —
    "\u2013": "-",    # en dash  –
    "\u2022": "*",    # bullet   •
    "\u00b7": ".",    # middle dot ·
    "\u20b9": "Rs.",  # rupee sign ₹
    "\u26a0": "(!)",  # warning  ⚠
    "\u2705": "[OK]", # check    ✅
    "\u2b50": "*",    # star     ⭐
    "\u2019": "'",    # right single quote '
    "\u2018": "'",    # left single quote  '
    "\u201c": '"',    # left double quote  "
    "\u201d": '"',    # right double quote "
    "\u2026": "...",  # ellipsis …
    "\u00b0": " deg", # degree   °
    "\u00d7": "x",    # multiply ×
    "\u00f7": "/",    # divide   ÷
    "\u2191": "^",    # up arrow ↑
    "\u2193": "v",    # down arrow ↓
}

def clean(text: str) -> str:
    """Replace all non-Latin-1 characters so Helvetica never errors."""
    if not text:
        return ""
    for char, replacement in _REPLACEMENTS.items():
        text = text.replace(char, replacement)
    # Final fallback: encode to latin-1, drop anything still unmappable
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ── Color helpers ─────────────────────────────────────────────────────────────
def _signal_color_rgb(signal: str):
    s = signal.upper()
    if "BUY"  in s: return (38, 166, 154)
    if "SELL" in s: return (239, 83, 80)
    return (255, 167, 38)


# ── PDF class ─────────────────────────────────────────────────────────────────
class StockReportPDF(FPDF):
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = clean(symbol)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(13, 17, 23)
        self.rect(0, 0, 210, 20, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(88, 166, 255)
        self.set_y(5)
        self.cell(0, 10, clean(f"STOCK ANALYSIS REPORT - {self.symbol}"), align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(139, 148, 158)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 5, clean(f"Generated {ts}  |  Page {self.page_no()}  |  (!) Not financial advice"), align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_fill_color(22, 27, 34)
        self.set_draw_color(88, 166, 255)
        self.set_line_width(0.5)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(88, 166, 255)
        self.cell(0, 8, clean(f"  {title}"), border="LB", fill=True, ln=True)
        self.ln(2)

    def kv_row(self, label: str, value: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(139, 148, 158)
        self.cell(70, 7, clean(label))
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(201, 209, 217)
        self.cell(0, 7, clean(str(value)), ln=True)

    def signal_badge(self, signal: str, score: int, confidence: int, price: float):
        r, g, b = _signal_color_rgb(signal)
        self.ln(3)
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        text = clean(f"  {signal}   |   Score: {score}   |   Confidence: {confidence}%   |   Rs.{price}")
        self.cell(0, 14, text, fill=True, ln=True, align="C")
        self.ln(3)

    def bullet_list(self, items: list, color_rgb=(201, 209, 217)):
        self.set_font("Helvetica", "", 10)
        r, g, b = color_rgb
        self.set_text_color(r, g, b)
        for item in items:
            self.cell(8, 6, "*")
            self.multi_cell(0, 6, clean(str(item)))
        self.ln(1)

    def divider_line(self):
        self.set_draw_color(48, 54, 61)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)


# ── Main export function ──────────────────────────────────────────────────────
def export_pdf(
    symbol: str,
    recommendation: dict,
    fundamentals: dict,
    news: list,
    output_path: str | None = None,
    chart_fig=None,
) -> str:
    """Generate and save a PDF analysis report. Returns the saved file path."""

    if not FPDF_AVAILABLE:
        return "fpdf2 not installed. Run: pip install fpdf2"

    if output_path is None:
        safe_sym = symbol.replace(".", "_")
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join("exports", f"{safe_sym}_{ts}.pdf")

    os.makedirs(
        os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
        exist_ok=True
    )

    pdf = StockReportPDF(symbol)
    pdf.add_page()

    # ── Company name + sector ─────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(201, 209, 217)
    pdf.ln(2)
    pdf.cell(0, 12, clean(fundamentals.get("name", symbol)), ln=True, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(139, 148, 158)
    sector   = clean(fundamentals.get("sector", ""))
    industry = clean(fundamentals.get("industry", ""))
    pdf.cell(0, 7, f"{sector}  |  {industry}", ln=True, align="C")
    pdf.ln(3)

    # ── Signal badge ──────────────────────────────────────────────────────────
    pdf.signal_badge(
        recommendation["signal"],
        recommendation["score"],
        recommendation["confidence"],
        recommendation["price"],
    )

    # ── Technical Summary ─────────────────────────────────────────────────────
    pdf.section_title("TECHNICAL SUMMARY")
    pdf.kv_row("Current Price",  f"Rs.{recommendation['price']}")
    pdf.kv_row("RSI (14)",       str(recommendation["rsi"]))
    pdf.kv_row("ADX (14)",       str(recommendation["adx"]))
    pdf.kv_row("Stochastic K",   str(recommendation.get("stoch_k", "N/A")))
    pdf.kv_row("MACD",           str(recommendation.get("macd", "N/A")))
    pdf.kv_row("MACD Signal",    str(recommendation.get("macd_signal", "N/A")))
    pdf.kv_row("Score",          str(recommendation["score"]))
    pdf.kv_row("Confidence",     f"{recommendation['confidence']}%")

    # ── Bullish Signals ───────────────────────────────────────────────────────
    reasons = recommendation.get("reasons", [])
    if reasons:
        pdf.section_title("BULLISH SIGNALS")
        pdf.bullet_list(reasons, color_rgb=(38, 166, 154))

    # ── Bearish / Risk Signals ────────────────────────────────────────────────
    warnings = recommendation.get("warnings", [])
    if warnings:
        pdf.section_title("BEARISH / RISK SIGNALS")
        pdf.bullet_list(warnings, color_rgb=(239, 83, 80))

    # ── Fundamentals ──────────────────────────────────────────────────────────
    pdf.section_title("COMPANY FUNDAMENTALS")
    labels = {
        "market_cap":     "Market Cap",
        "pe_ratio":       "P/E Ratio",
        "pb_ratio":       "P/B Ratio",
        "eps":            "EPS (TTM)",
        "dividend_yield": "Dividend Yield",
        "52w_high":       "52-Week High",
        "52w_low":        "52-Week Low",
        "avg_volume":     "Avg. Volume",
        "beta":           "Beta",
        "roe":            "Return on Equity",
        "debt_to_equity": "Debt / Equity",
    }
    skip = {"name", "sector", "industry", "description", "error"}
    for key, label in labels.items():
        if key in fundamentals and key not in skip:
            pdf.kv_row(label, str(fundamentals[key]))

    # ── Business Description ──────────────────────────────────────────────────
    desc = fundamentals.get("description", "")
    if desc and desc != "N/A":
        pdf.section_title("ABOUT THE COMPANY")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(139, 148, 158)
        truncated = clean(desc[:600] + ("..." if len(desc) > 600 else ""))
        pdf.multi_cell(0, 5, truncated)

    # ── Recent News ───────────────────────────────────────────────────────────
    if news:
        pdf.section_title("RECENT NEWS")
        for item in news[:5]:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(88, 166, 255)
            pdf.multi_cell(0, 5, clean(item.get("title", "")))

            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(139, 148, 158)
            pdf.cell(0, 5, clean(f"Source: {item.get('source', 'N/A')}"), ln=True)

            summary = item.get("summary", "")
            if summary:
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(139, 148, 158)
                pdf.multi_cell(0, 5, clean(summary[:200] + ("..." if len(summary) > 200 else "")))

            pdf.divider_line()

    # ── Disclaimer ────────────────────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, clean(
        "DISCLAIMER: This report is generated by an AI system for informational "
        "purposes only. It does not constitute financial advice. Always do your "
        "own research and consult a qualified financial advisor before making "
        "investment decisions."
    ))

    pdf.output(output_path)
    return output_path
