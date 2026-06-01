import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to the OHLCV dataframe."""

    close  = data["Close"]
    high   = data["High"]
    low    = data["Low"]
    volume = data["Volume"]

    # ── RSI ───────────────────────────────────────────────────────────────────
    data["RSI"] = RSIIndicator(close=close, window=14).rsi()

    # ── Stochastic ────────────────────────────────────────────────────────────
    stoch = StochasticOscillator(high=high, low=low, close=close, window=14)
    data["STOCH_K"] = stoch.stoch()
    data["STOCH_D"] = stoch.stoch_signal()

    # ── SMA ───────────────────────────────────────────────────────────────────
    data["SMA20"]  = SMAIndicator(close=close, window=20).sma_indicator()
    data["SMA50"]  = SMAIndicator(close=close, window=50).sma_indicator()
    data["SMA200"] = SMAIndicator(close=close, window=200).sma_indicator()

    # ── EMA ───────────────────────────────────────────────────────────────────
    data["EMA20"] = EMAIndicator(close=close, window=20).ema_indicator()
    data["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()

    # ── MACD ──────────────────────────────────────────────────────────────────
    macd = MACD(close=close)
    data["MACD"]        = macd.macd()
    data["MACD_SIGNAL"] = macd.macd_signal()
    data["MACD_HIST"]   = macd.macd_diff()

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    bb = BollingerBands(close=close, window=20)
    data["BB_HIGH"] = bb.bollinger_hband()
    data["BB_MID"]  = bb.bollinger_mavg()
    data["BB_LOW"]  = bb.bollinger_lband()
    data["BB_WIDTH"]= bb.bollinger_wband()

    # ── ATR ───────────────────────────────────────────────────────────────────
    data["ATR"] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()

    # ── ADX ───────────────────────────────────────────────────────────────────
    adx = ADXIndicator(high=high, low=low, close=close, window=14)
    data["ADX"]    = adx.adx()
    data["ADX_POS"] = adx.adx_pos()
    data["ADX_NEG"] = adx.adx_neg()

    # ── Volume SMA ────────────────────────────────────────────────────────────
    data["VOLUME_SMA20"] = SMAIndicator(close=volume, window=20).sma_indicator()

    # ── Price Change % ────────────────────────────────────────────────────────
    data["PCT_CHANGE"] = close.pct_change() * 100

    return data
