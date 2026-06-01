from langchain.tools import tool

from tools.stock_fetcher import fetch_stock_data, fetch_fundamentals, fetch_news
from tools.indicators import add_indicators
from tools.recommender import get_recommendation
from utils.charts import plot_stock, plot_comparison, build_stock_chart_html, build_comparison_chart_html
from utils.pdf_exporter import export_pdf

import os

# Detect whether we're running inside a web server (Flask) or the CLI agent.
# When FLASK_ENV or PORT is set (Render sets PORT automatically), skip fig.show().
_WEB_MODE = bool(os.getenv("PORT") or os.getenv("FLASK_ENV") or os.getenv("WEB_MODE"))


def _ensure_ns(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if ".NS" not in symbol and ".BO" not in symbol:
        symbol += ".NS"
    return symbol


# ─────────────────────────────────────────────────────────────────────────────
# 1. TECHNICAL ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
@tool
def analyze_stock(symbol: str) -> str:
    """
    Full technical analysis of an Indian stock.
    Returns: price, RSI, ADX, MACD, Stochastic, score, Buy/Hold/Sell signal and reasons.
    Use for any technical analysis or recommendation query.
    Example input: 'TCS' or 'RELIANCE' or 'INFY.NS'
    """
    symbol = _ensure_ns(symbol)
    data = fetch_stock_data(symbol)
    if data is None or data.empty:
        return f"Could not fetch data for {symbol}. Check the symbol."

    data = add_indicators(data)
    r    = get_recommendation(data)

    lines = [
        f"TECHNICAL ANALYSIS — {symbol}",
        f"",
        f"  Current Price  : ₹{r['price']}",
        f"  RSI (14)       : {r['rsi']}",
        f"  ADX (14)       : {r['adx']}",
        f"  Stochastic K   : {r['stoch_k']}",
        f"  MACD           : {r['macd']}",
        f"  MACD Signal    : {r['macd_signal']}",
        f"  Score          : {r['score']}",
        f"  Confidence     : {r['confidence']}%",
        f"  Signal         : *** {r['signal']} ***",
        f"",
        f"Bullish Signals:",
    ]
    for reason in r["reasons"]:
        lines.append(f"  ✅ {reason}")
    lines.append("")
    lines.append("Bearish / Risk Signals:")
    for w in r["warnings"]:
        lines.append(f"  ⚠️  {w}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 2. FUNDAMENTALS
# ─────────────────────────────────────────────────────────────────────────────
@tool
def get_fundamentals(symbol: str) -> str:
    """
    Get fundamental / valuation data for an Indian stock.
    Returns: P/E, P/B, EPS, Market Cap, Dividend Yield, 52W High/Low, Beta, ROE, Debt/Equity, sector.
    Use when user asks about company financials, valuation, or fundamentals.
    Example input: 'HDFCBANK' or 'WIPRO'
    """
    symbol = _ensure_ns(symbol)
    f = fetch_fundamentals(symbol)

    if "error" in f:
        return f"Could not fetch fundamentals for {symbol}: {f['error']}"

    lines = [
        f"FUNDAMENTALS — {f.get('name', symbol)}",
        f"",
        f"  Sector           : {f.get('sector', 'N/A')}",
        f"  Industry         : {f.get('industry', 'N/A')}",
        f"  Market Cap       : {f.get('market_cap', 'N/A')}",
        f"  P/E Ratio        : {f.get('pe_ratio', 'N/A')}",
        f"  P/B Ratio        : {f.get('pb_ratio', 'N/A')}",
        f"  EPS (TTM)        : {f.get('eps', 'N/A')}",
        f"  Dividend Yield   : {f.get('dividend_yield', 'N/A')}",
        f"  52-Week High     : ₹{f.get('52w_high', 'N/A')}",
        f"  52-Week Low      : ₹{f.get('52w_low', 'N/A')}",
        f"  Beta             : {f.get('beta', 'N/A')}",
        f"  ROE              : {f.get('roe', 'N/A')}",
        f"  Debt / Equity    : {f.get('debt_to_equity', 'N/A')}",
        f"  Avg Daily Volume : {f.get('avg_volume', 'N/A')}",
    ]

    desc = f.get("description", "")
    if desc and desc != "N/A":
        lines += ["", "About:", desc[:400] + "..."]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 3. COMPARE STOCKS
# ─────────────────────────────────────────────────────────────────────────────
@tool
def compare_stocks(symbols: str) -> str:
    """
    Compare multiple Indian stocks side by side (technical + price).
    Input: comma-separated stock symbols e.g. 'TCS,INFY,WIPRO'
    Shows price, RSI, signal, score and confidence for each stock.
    Use when user asks to compare or rank stocks.
    """
    sym_list = [_ensure_ns(s.strip()) for s in symbols.split(",") if s.strip()]
    if len(sym_list) < 2:
        return "Please provide at least 2 comma-separated symbols to compare."

    rows = []
    for sym in sym_list:
        data = fetch_stock_data(sym)
        if data is None or data.empty:
            rows.append(f"  {sym:<15} — Could not fetch data")
            continue
        data = add_indicators(data)
        r = get_recommendation(data)
        rows.append(
            f"  {sym:<15} ₹{r['price']:<10} RSI={r['rsi']:<7} "
            f"Score={r['score']:<5} {r['signal']:<12} Confidence={r['confidence']}%"
        )

    header = (
        f"  {'SYMBOL':<15} {'PRICE':<10} {'RSI':<13} "
        f"{'SCORE':<10} {'SIGNAL':<12} CONFIDENCE"
    )
    divider = "  " + "─" * 75

    return "\n".join([
        "STOCK COMPARISON",
        "",
        header,
        divider,
        *rows,
        "",
        "Tip: Use 'show_chart' for a detailed chart of any of the above stocks."
    ])


# ─────────────────────────────────────────────────────────────────────────────
# 4. SHOW CHART
# ─────────────────────────────────────────────────────────────────────────────
@tool
def show_chart(symbol: str) -> str:
    """
    Display a full interactive technical analysis chart for an Indian stock.
    4 panels: Candlestick + EMA/BB, Volume, RSI, MACD.
    Use when user asks to 'show chart', 'plot', or 'visualize' a stock.
    Example input: 'TATAMOTORS'
    """
    symbol = _ensure_ns(symbol)
    data = fetch_stock_data(symbol)
    if data is None or data.empty:
        return f"Could not fetch data for {symbol}."

    data = add_indicators(data)
    rec  = get_recommendation(data)

    if _WEB_MODE:
        # In web/Render mode: return HTML so the caller can embed it
        chart_html = build_stock_chart_html(data, symbol, rec)
        return f"CHART_HTML:{chart_html}|||Signal: {rec['signal']} | Confidence: {rec['confidence']}%"
    else:
        # CLI mode: open in browser as before
        plot_stock(data, symbol, recommendation=rec)
        return f"Chart displayed for {symbol} — Signal: {rec['signal']} | Confidence: {rec['confidence']}%"


# ─────────────────────────────────────────────────────────────────────────────
# 5. COMPARE CHART
# ─────────────────────────────────────────────────────────────────────────────
@tool
def show_comparison_chart(symbols: str) -> str:
    """
    Display a normalised return comparison chart for multiple stocks.
    All stocks are indexed to 100 so % returns are directly comparable.
    Input: comma-separated symbols e.g. 'RELIANCE,TCS,HDFCBANK'
    Use when user wants to visually compare stock performance.
    """
    sym_list = [_ensure_ns(s.strip()) for s in symbols.split(",") if s.strip()]
    if len(sym_list) < 2:
        return "Please provide at least 2 comma-separated symbols."

    stocks_data = {}
    for sym in sym_list:
        data = fetch_stock_data(sym)
        if data is not None and not data.empty:
            stocks_data[sym] = data

    if not stocks_data:
        return "Could not fetch data for any of the provided symbols."

    if _WEB_MODE:
        chart_html = build_comparison_chart_html(stocks_data)
        return f"CHART_HTML:{chart_html}|||Comparison chart for: {', '.join(stocks_data.keys())}"
    else:
        plot_comparison(stocks_data)
        return f"Comparison chart displayed for: {', '.join(stocks_data.keys())}"


# ─────────────────────────────────────────────────────────────────────────────
# 6. NEWS SENTIMENT
# ─────────────────────────────────────────────────────────────────────────────
@tool
def get_news(symbol: str) -> str:
    """
    Get the latest news headlines for an Indian stock.
    Returns up to 5 recent headlines with source and summary.
    Use when user asks about recent news, events, or sentiment for a stock.
    Example input: 'BAJFINANCE'
    """
    symbol = _ensure_ns(symbol)
    news   = fetch_news(symbol, max_items=5)

    if not news:
        return f"No recent news found for {symbol}."

    lines = [f"RECENT NEWS — {symbol}", ""]
    for i, item in enumerate(news, 1):
        lines.append(f"  {i}. {item.get('title', 'No title')}")
        lines.append(f"     Source  : {item.get('source', 'N/A')}")
        summary = item.get("summary", "")
        if summary:
            lines.append(f"     Summary : {summary[:200]}{'...' if len(summary) > 200 else ''}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 7. EXPORT PDF REPORT
# ─────────────────────────────────────────────────────────────────────────────
@tool
def export_report(symbol: str) -> str:
    """
    Generate and save a professional PDF analysis report for a stock.
    The report includes: signal badge, technical summary, fundamentals,
    bullish/bearish signals, recent news, and a disclaimer.
    Saved to the exports/ folder.
    Use when user says 'export report', 'save PDF', 'generate report' for a stock.
    Example input: 'SBIN'
    """
    symbol = _ensure_ns(symbol)

    data = fetch_stock_data(symbol)
    if data is None or data.empty:
        return f"Could not fetch data for {symbol}."

    data   = add_indicators(data)
    rec    = get_recommendation(data)
    fund   = fetch_fundamentals(symbol)
    news   = fetch_news(symbol)

    path = export_pdf(
        symbol=symbol,
        recommendation=rec,
        fundamentals=fund,
        news=news,
    )

    return (
        f"PDF report saved to: {path}\n"
        f"Signal: {rec['signal']} | Score: {rec['score']} | Confidence: {rec['confidence']}%"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. SCREENER
# ─────────────────────────────────────────────────────────────────────────────
@tool
def screen_stocks(symbols: str) -> str:
    """
    Screen a list of stocks and rank them by technical score.
    Only shows BUY or STRONG BUY candidates at the top.
    Input: comma-separated symbols e.g. 'TCS,INFY,WIPRO,HDFCBANK,RELIANCE,SBIN'
    Use when user wants to find the best stocks from a list.
    """
    sym_list = [_ensure_ns(s.strip()) for s in symbols.split(",") if s.strip()]
    results  = []

    for sym in sym_list:
        data = fetch_stock_data(sym)
        if data is None or data.empty:
            continue
        data = add_indicators(data)
        r    = get_recommendation(data)
        results.append((sym, r))

    results.sort(key=lambda x: x[1]["score"], reverse=True)

    lines = ["STOCK SCREENER — Ranked by Technical Score", ""]
    lines.append(f"  {'RANK':<6}{'SYMBOL':<15}{'PRICE':<12}{'SCORE':<8}{'SIGNAL':<15}CONF%")
    lines.append("  " + "─" * 65)

    for rank, (sym, r) in enumerate(results, 1):
        flag = "⭐" if r["signal"] in ("BUY", "STRONG BUY") else "  "
        lines.append(
            f"  {rank:<6}{sym:<15}₹{r['price']:<11}{r['score']:<8}{r['signal']:<15}{r['confidence']}% {flag}"
        )

    lines += ["", "⭐ = BUY or STRONG BUY candidate"]
    return "\n".join(lines)
