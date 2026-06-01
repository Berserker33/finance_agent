import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Palette ───────────────────────────────────────────────────────────────────
DARK_BG     = "#0d1117"
PANEL_BG    = "#161b22"
GRID        = "rgba(255,255,255,0.05)"
UP          = "#26a69a"
DOWN        = "#ef5350"
EMA20_COL   = "#FFA726"
EMA50_COL   = "#AB47BC"
BB_LINE     = "#64B5F6"
BB_FILL     = "rgba(100,181,246,0.08)"
RSI_COL     = "#29B6F6"
MACD_COL    = "#26a69a"
SIG_COL     = "#FF7043"
VOL_UP      = "rgba(38,166,154,0.55)"
VOL_DN      = "rgba(239,83,80,0.55)"
VOL_SMA_COL = "#FFEB3B"
TEXT_DIM    = "#8b949e"
TEXT_MAIN   = "#c9d1d9"


def _signal_color(signal: str) -> str:
    s = signal.upper()
    if "BUY"  in s: return UP
    if "SELL" in s: return DOWN
    return "#FFA726"


def _build_stock_figure(data: pd.DataFrame, symbol: str, recommendation: dict | None = None) -> go.Figure:
    """Build and return the Plotly Figure (shared by both show and export)."""
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=(
            f"<b>{symbol}</b> — Price & Indicators",
            "Volume",
            "RSI (14)",
            "MACD (12, 26, 9)"
        )
    )

    # Panel 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"], high=data["High"],
        low=data["Low"],   close=data["Close"],
        name="Price",
        increasing=dict(line=dict(color=UP,   width=1), fillcolor=UP),
        decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=DOWN),
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["EMA20"],
        mode="lines", name="EMA 20",
        line=dict(color=EMA20_COL, width=1.5)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["EMA50"],
        mode="lines", name="EMA 50",
        line=dict(color=EMA50_COL, width=1.5)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["BB_HIGH"],
        mode="lines", name="BB Upper",
        line=dict(color=BB_LINE, width=1, dash="dot"),
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["BB_LOW"],
        mode="lines", name="BB Lower",
        line=dict(color=BB_LINE, width=1, dash="dot"),
        fill="tonexty", fillcolor=BB_FILL,
    ), row=1, col=1)

    if "SMA200" in data.columns:
        fig.add_trace(go.Scatter(
            x=data["Date"], y=data["SMA200"],
            mode="lines", name="SMA 200",
            line=dict(color="#FF5252", width=1, dash="dash"),
        ), row=1, col=1)

    # Panel 2: Volume
    vol_colors = [
        VOL_UP if c >= o else VOL_DN
        for c, o in zip(data["Close"], data["Open"])
    ]
    fig.add_trace(go.Bar(
        x=data["Date"], y=data["Volume"],
        name="Volume",
        marker_color=vol_colors,
        showlegend=False
    ), row=2, col=1)

    if "VOLUME_SMA20" in data.columns:
        fig.add_trace(go.Scatter(
            x=data["Date"], y=data["VOLUME_SMA20"],
            mode="lines", name="Vol SMA20",
            line=dict(color=VOL_SMA_COL, width=1.2)
        ), row=2, col=1)

    # Panel 3: RSI
    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["RSI"],
        mode="lines", name="RSI",
        line=dict(color=RSI_COL, width=1.5)
    ), row=3, col=1)

    for level, color in [(70, "rgba(239,83,80,0.5)"), (50, "rgba(255,255,255,0.15)"), (30, "rgba(38,166,154,0.5)")]:
        fig.add_hline(y=level, line_dash="dash", line_color=color, line_width=1, row=3, col=1)

    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.05)",  line_width=0, row=3, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(38,166,154,0.05)", line_width=0, row=3, col=1)

    # Panel 4: MACD
    hist = data["MACD"] - data["MACD_SIGNAL"]
    hist_colors = [
        "rgba(38,166,154,0.75)" if v >= 0 else "rgba(239,83,80,0.75)"
        for v in hist
    ]
    fig.add_trace(go.Bar(
        x=data["Date"], y=hist,
        name="MACD Hist",
        marker_color=hist_colors,
        showlegend=False
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["MACD"],
        mode="lines", name="MACD",
        line=dict(color=MACD_COL, width=1.5)
    ), row=4, col=1)

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["MACD_SIGNAL"],
        mode="lines", name="Signal",
        line=dict(color=SIG_COL, width=1.5)
    ), row=4, col=1)

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1, row=4, col=1)

    # Recommendation badge
    if recommendation:
        sig   = recommendation.get("signal", "")
        score = recommendation.get("score", 0)
        conf  = recommendation.get("confidence", 0)
        price = recommendation.get("price", "")
        color = _signal_color(sig)
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.99, y=0.99,
            text=f"<b> {sig} </b>  ·  Score {score}  ·  Confidence {conf}%  ·  ₹{price}",
            showarrow=False,
            font=dict(size=12, color="white", family="monospace"),
            align="right",
            bgcolor=color,
            bordercolor=color,
            borderwidth=2,
            borderpad=8,
            opacity=0.92
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="'JetBrains Mono', monospace", size=11, color=TEXT_MAIN),
        title=dict(
            text=f"<b>{symbol}</b> — Technical Analysis Dashboard",
            font=dict(size=17, color="#58a6ff"),
            x=0.5
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0, font=dict(size=10),
            bgcolor="rgba(0,0,0,0)"
        ),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        height=900,
        margin=dict(l=60, r=40, t=80, b=40),
        hoverlabel=dict(bgcolor=PANEL_BG, font_size=11, font_family="monospace")
    )

    for r in range(1, 5):
        fig.update_xaxes(showgrid=True, gridcolor=GRID, row=r, col=1)
        fig.update_yaxes(showgrid=True, gridcolor=GRID, row=r, col=1)

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume",    row=2, col=1)
    fig.update_yaxes(title_text="RSI",       row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD",      row=4, col=1)

    return fig


def _build_comparison_figure(stocks_data: dict, metric: str = "Close") -> go.Figure:
    """Build and return the comparison Plotly Figure."""
    fig = go.Figure()
    colors = ["#26a69a", "#FFA726", "#AB47BC", "#29B6F6", "#FF5252", "#FFEB3B"]

    for i, (sym, data) in enumerate(stocks_data.items()):
        series    = data[metric].dropna()
        normalised = (series / series.iloc[0]) * 100
        fig.add_trace(go.Scatter(
            x=data["Date"],
            y=normalised,
            mode="lines",
            name=sym,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f"<b>{sym}</b><br>Return: %{{y:.1f}}%<extra></extra>"
        ))

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family="monospace", size=11, color=TEXT_MAIN),
        title=dict(
            text="<b>Stock Comparison</b> — Normalised Returns (base = 100)",
            font=dict(size=16, color="#58a6ff"), x=0.5
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        hovermode="x unified",
        height=500,
        margin=dict(l=60, r=40, t=80, b=40),
        xaxis=dict(showgrid=True, gridcolor=GRID),
        yaxis=dict(showgrid=True, gridcolor=GRID, title="Normalised Price (%)"),
    )
    return fig


# ── Public API ─────────────────────────────────────────────────────────────────

def plot_stock(data: pd.DataFrame, symbol: str, recommendation: dict | None = None):
    """CLI: open the chart in a browser window (used by agent.py)."""
    _build_stock_figure(data, symbol, recommendation).show()


def plot_comparison(stocks_data: dict, metric: str = "Close"):
    """CLI: open the comparison chart in a browser window (used by agent.py)."""
    _build_comparison_figure(stocks_data, metric).show()


def build_stock_chart_html(data: pd.DataFrame, symbol: str, recommendation: dict | None = None) -> str:
    """Flask/web: return a self-contained HTML div string (no CDN needed — Plotly already on page)."""
    fig = _build_stock_figure(data, symbol, recommendation)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_comparison_chart_html(stocks_data: dict, metric: str = "Close") -> str:
    """Flask/web: return a self-contained HTML div string."""
    fig = _build_comparison_figure(stocks_data, metric)
    return fig.to_html(full_html=False, include_plotlyjs=False)
