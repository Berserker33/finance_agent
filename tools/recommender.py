import pandas as pd


def get_recommendation(data: pd.DataFrame) -> dict:
    """
    Score-based recommendation engine using multiple technical signals.
    Returns a full dict with signal, score, confidence, and reasons.
    """
    latest = data.iloc[-1]
    prev   = data.iloc[-2] if len(data) > 1 else latest

    score   = 0
    reasons = []
    warnings = []

    # ── RSI ───────────────────────────────────────────────────────────────────
    rsi = latest["RSI"]
    if rsi < 30:
        score += 2
        reasons.append(f"RSI {rsi:.1f} — oversold, potential reversal upward")
    elif rsi > 70:
        score -= 2
        warnings.append(f"RSI {rsi:.1f} — overbought, potential reversal downward")
    elif 45 <= rsi <= 55:
        reasons.append(f"RSI {rsi:.1f} — neutral zone")

    # ── Stochastic ────────────────────────────────────────────────────────────
    stoch_k = latest["STOCH_K"]
    stoch_d = latest["STOCH_D"]
    if stoch_k < 20 and stoch_d < 20:
        score += 1
        reasons.append("Stochastic in oversold territory (K & D < 20)")
    elif stoch_k > 80 and stoch_d > 80:
        score -= 1
        warnings.append("Stochastic in overbought territory (K & D > 80)")

    # ── EMA Crossover ─────────────────────────────────────────────────────────
    if latest["EMA20"] > latest["EMA50"]:
        score += 2
        reasons.append("EMA20 above EMA50 — short-term bullish momentum")
    else:
        score -= 2
        warnings.append("EMA20 below EMA50 — short-term bearish momentum")

    # ── Golden / Death Cross (SMA50 vs SMA200) ────────────────────────────────
    if latest["SMA50"] > latest["SMA200"]:
        score += 2
        reasons.append("SMA50 above SMA200 — Golden Cross (long-term bullish)")
    else:
        score -= 2
        warnings.append("SMA50 below SMA200 — Death Cross (long-term bearish)")

    # ── Price vs SMA200 ───────────────────────────────────────────────────────
    if latest["Close"] > latest["SMA200"]:
        score += 1
        reasons.append("Price above SMA200 — long-term uptrend intact")
    else:
        score -= 1
        warnings.append("Price below SMA200 — long-term downtrend")

    # ── MACD ──────────────────────────────────────────────────────────────────
    if latest["MACD"] > latest["MACD_SIGNAL"]:
        score += 2
        if prev["MACD"] <= prev["MACD_SIGNAL"]:
            reasons.append("MACD fresh bullish crossover — strong buy signal")
        else:
            reasons.append("MACD above signal line — bullish momentum")
    else:
        score -= 2
        if prev["MACD"] >= prev["MACD_SIGNAL"]:
            warnings.append("MACD fresh bearish crossover — strong sell signal")
        else:
            warnings.append("MACD below signal line — bearish momentum")

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    if latest["Close"] < latest["BB_LOW"]:
        score += 1
        reasons.append("Price at lower Bollinger Band — potential bounce zone")
    elif latest["Close"] > latest["BB_HIGH"]:
        score -= 1
        warnings.append("Price at upper Bollinger Band — potential resistance")

    # ── ADX Trend Strength ────────────────────────────────────────────────────
    adx = latest["ADX"]
    if adx > 25:
        score += 1
        reasons.append(f"ADX {adx:.1f} — strong trend in play")
    elif adx < 15:
        warnings.append(f"ADX {adx:.1f} — weak/no trend, choppy market")

    # DI+ vs DI-
    if latest["ADX_POS"] > latest["ADX_NEG"]:
        score += 1
        reasons.append("DI+ above DI- — positive directional bias")
    else:
        score -= 1
        warnings.append("DI- above DI+ — negative directional bias")

    # ── Volume ────────────────────────────────────────────────────────────────
    if latest["Volume"] > latest["VOLUME_SMA20"]:
        score += 1
        reasons.append("Above-average volume — conviction behind the move")
    else:
        warnings.append("Below-average volume — weak conviction")

    # ── Final Signal ──────────────────────────────────────────────────────────
    if score >= 7:
        signal = "STRONG BUY"
    elif score >= 4:
        signal = "BUY"
    elif score <= -6:
        signal = "STRONG SELL"
    elif score <= -3:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(max(int((score + 12) * 4.16), 0), 100)

    return {
        "price":      round(float(latest["Close"]), 2),
        "rsi":        round(float(rsi), 2),
        "adx":        round(float(adx), 2),
        "stoch_k":    round(float(stoch_k), 2),
        "macd":       round(float(latest["MACD"]), 4),
        "macd_signal":round(float(latest["MACD_SIGNAL"]), 4),
        "score":      score,
        "confidence": confidence,
        "signal":     signal,
        "reasons":    reasons,
        "warnings":   warnings,
    }
