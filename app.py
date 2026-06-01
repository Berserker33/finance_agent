"""
Flask Web UI for the Finance AI Agent.
Run locally : python app.py
Deploy (Render): gunicorn app:app
"""
import os, json, traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from tools.finance_tools import (
    analyze_stock, get_fundamentals, compare_stocks,
    show_chart, show_comparison_chart, get_news,
    export_report, screen_stocks,
)
from tools.stock_fetcher import fetch_stock_data, fetch_fundamentals, fetch_news
from tools.indicators import add_indicators
from tools.recommender import get_recommendation
from utils.charts import build_stock_chart_html, build_comparison_chart_html
from utils.pdf_exporter import export_pdf

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "financegpt-secret")


def get_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")


def _ensure_ns(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if ".NS" not in symbol and ".BO" not in symbol:
        symbol += ".NS"
    return symbol


def build_agent():
    llm = ChatGroq(
        groq_api_key=get_api_key(),
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
    )
    tools = [
        analyze_stock, get_fundamentals, compare_stocks,
        show_chart, show_comparison_chart, get_news,
        export_report, screen_stocks,
    ]
    react_template = """You are FinanceGPT, an expert AI financial analyst specialising in Indian stocks (NSE/BSE).

You have access to these tools:
{tools}

TOOL SELECTION GUIDE:
- "analyze TCS"            → analyze_stock
- "fundamentals of HDFC"   → get_fundamentals
- "compare TCS vs INFY"    → compare_stocks (input: "TCS,INFY")
- "chart for RELIANCE"     → show_chart
- "compare chart TCS,INFY" → show_comparison_chart
- "news for BAJFINANCE"    → get_news
- "screen TCS,INFY,WIPRO"  → screen_stocks
- "export report for SBIN" → export_report

STRICT FORMAT:
Question: the input question
Thought: reason step by step
Action: one of [{tool_names}]
Action Input: symbol or symbols only
Observation: result of the action
... (repeat as needed)
Thought: I now know the final answer
Final Answer: clear, well-structured response with key findings, signal, reasoning, caveats.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    prompt = PromptTemplate.from_template(react_template)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=agent, tools=tools, verbose=False,
        handle_parsing_errors=True, max_iterations=6,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400
    try:
        executor = build_agent()
        result = executor.invoke({"input": query})
        return jsonify({"output": result["output"]})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data   = request.get_json(force=True)
    symbol = _ensure_ns(data.get("symbol", ""))
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
    try:
        df   = fetch_stock_data(symbol)
        if df is None or df.empty:
            return jsonify({"error": f"No data for {symbol}"}), 404
        df   = add_indicators(df)
        rec  = get_recommendation(df)
        fund = fetch_fundamentals(symbol)
        news = fetch_news(symbol, max_items=5)
        chart_html = build_stock_chart_html(df, symbol, rec)
        return jsonify({
            "symbol": symbol,
            "recommendation": rec,
            "fundamentals": fund,
            "news": news,
            "chart_html": chart_html,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def compare():
    data     = request.get_json(force=True)
    raw      = data.get("symbols", "")
    sym_list = [_ensure_ns(s) for s in raw.split(",") if s.strip()]
    if len(sym_list) < 2:
        return jsonify({"error": "At least 2 symbols required"}), 400
    try:
        rows        = []
        stocks_data = {}
        for sym in sym_list:
            df = fetch_stock_data(sym)
            if df is not None and not df.empty:
                df = add_indicators(df)
                r  = get_recommendation(df)
                stocks_data[sym] = df
                rows.append({
                    "symbol":     sym,
                    "price":      r["price"],
                    "rsi":        r["rsi"],
                    "adx":        r["adx"],
                    "score":      r["score"],
                    "signal":     r["signal"],
                    "confidence": r["confidence"],
                })
        rows.sort(key=lambda x: x["score"], reverse=True)
        chart_html = build_comparison_chart_html(stocks_data) if stocks_data else ""
        return jsonify({"rows": rows, "chart_html": chart_html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/screen", methods=["POST"])
def screen():
    data     = request.get_json(force=True)
    raw      = data.get("symbols", "")
    sym_list = [_ensure_ns(s) for s in raw.split(",") if s.strip()]
    if not sym_list:
        return jsonify({"error": "No symbols provided"}), 400
    try:
        results = []
        for sym in sym_list:
            df = fetch_stock_data(sym)
            if df is not None and not df.empty:
                df = add_indicators(df)
                r  = get_recommendation(df)
                results.append({
                    "symbol":     sym,
                    "price":      r["price"],
                    "rsi":        r["rsi"],
                    "adx":        r["adx"],
                    "score":      r["score"],
                    "signal":     r["signal"],
                    "confidence": r["confidence"],
                    "is_buy":     "BUY" in r["signal"],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export_pdf", methods=["POST"])
def export_pdf_route():
    data   = request.get_json(force=True)
    symbol = _ensure_ns(data.get("symbol", ""))
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400
    try:
        df   = fetch_stock_data(symbol)
        if df is None or df.empty:
            return jsonify({"error": f"No data for {symbol}"}), 404
        df   = add_indicators(df)
        rec  = get_recommendation(df)
        fund = fetch_fundamentals(symbol)
        news = fetch_news(symbol)
        path = export_pdf(symbol=symbol, recommendation=rec, fundamentals=fund, news=news)
        return jsonify({"path": path, "signal": rec["signal"], "score": rec["score"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/exports/<path:filename>")
def serve_export(filename):
    return send_from_directory("exports", filename)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
