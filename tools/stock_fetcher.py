import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol: str, period: str = "6mo") -> pd.DataFrame | None:
    """Fetch OHLCV data for a given symbol from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        if data.empty:
            return None
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        print(f"[stock_fetcher] Error fetching {symbol}: {e}")
        return None


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental/company info from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        def safe(key, default="N/A"):
            val = info.get(key, default)
            return val if val not in (None, "", 0) else default

        market_cap = safe("marketCap")
        if market_cap != "N/A":
            market_cap = f"₹{int(market_cap):,}"

        return {
            "name":             safe("longName"),
            "sector":           safe("sector"),
            "industry":         safe("industry"),
            "market_cap":       market_cap,
            "pe_ratio":         round(float(safe("trailingPE", 0) or 0), 2),
            "pb_ratio":         round(float(safe("priceToBook", 0) or 0), 2),
            "eps":              round(float(safe("trailingEps", 0) or 0), 2),
            "dividend_yield":   f"{round(float(safe('dividendYield', 0) or 0) * 100, 2)}%",
            "52w_high":         round(float(safe("fiftyTwoWeekHigh", 0) or 0), 2),
            "52w_low":          round(float(safe("fiftyTwoWeekLow", 0) or 0), 2),
            "avg_volume":       safe("averageVolume"),
            "beta":             round(float(safe("beta", 0) or 0), 2),
            "roe":              f"{round(float(safe('returnOnEquity', 0) or 0) * 100, 2)}%",
            "debt_to_equity":   round(float(safe("debtToEquity", 0) or 0), 2),
            "description":      safe("longBusinessSummary"),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_news(symbol: str, max_items: int = 5) -> list[dict]:
    """Fetch recent news headlines for a stock."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        results = []
        for item in news[:max_items]:
            content = item.get("content", {})
            title = content.get("title", item.get("title", "No title"))
            provider = content.get("provider", {})
            source = provider.get("displayName", "Unknown") if isinstance(provider, dict) else "Unknown"
            results.append({
                "title":    title,
                "source":   source,
                "summary":  content.get("summary", ""),
            })
        return results
    except Exception as e:
        return [{"title": f"Error fetching news: {e}", "source": "", "summary": ""}]
