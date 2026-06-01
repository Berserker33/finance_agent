from dotenv import load_dotenv
import os
from datetime import datetime

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from tools.finance_tools import (
    analyze_stock,
    get_fundamentals,
    compare_stocks,
    show_chart,
    show_comparison_chart,
    get_news,
    screen_stocks,
)

# ── Terminal Colors ────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m";  DIM     = "\033[2m"
    GREEN   = "\033[92m"; YELLOW  = "\033[93m"; CYAN    = "\033[96m"
    RED     = "\033[91m"; BLUE    = "\033[94m"; MAGENTA = "\033[95m"
    WHITE   = "\033[97m"

def divider(char="─", width=64, color=C.DIM):
    print(f"{color}{char * width}{C.RESET}")

def header(title: str):
    divider("═")
    pad = max((62 - len(title)) // 2, 0)
    print(f"{C.BOLD}{C.CYAN}{'═'}{' ' * pad}{title}{' ' * pad}{'═'}{C.RESET}")
    divider("═")

def section(title: str):
    print(f"\n{C.BOLD}{C.YELLOW}▸ {title}{C.RESET}")
    divider("─", 52)

def publish_results(query: str, output: str, elapsed_ms: int):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    print()
    header("FINANCE AI  —  ANALYSIS REPORT")

    section("Query")
    print(f"  {C.DIM}{'Query':<20}{C.RESET}{C.WHITE}{query}{C.RESET}")
    print(f"  {C.DIM}{'Generated':<20}{C.RESET}{C.DIM}{now}{C.RESET}")
    print(f"  {C.DIM}{'Duration':<20}{C.RESET}{C.DIM}{elapsed_ms} ms{C.RESET}")

    section("Result")
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if any(w in low for w in ["strong buy", "buy", "bullish", "oversold", "upside", "✅"]):
            print(f"  {C.GREEN}▲  {line}{C.RESET}")
        elif any(w in low for w in ["strong sell", "sell", "bearish", "overbought", "⚠"]):
            print(f"  {C.RED}▼  {line}{C.RESET}")
        elif any(w in low for w in ["hold", "neutral", "stable"]):
            print(f"  {C.YELLOW}●  {line}{C.RESET}")
        elif line.startswith("—") or line.isupper() or line.endswith(":"):
            print(f"\n  {C.BOLD}{C.CYAN}{line}{C.RESET}")
        else:
            print(f"  {C.WHITE}{line}{C.RESET}")

    print()
    divider("═")
    print(f"  {C.DIM}⚠  AI-generated analysis. Not financial advice.{C.RESET}")
    divider("═")
    print()


# ── Setup ──────────────────────────────────────────────────────────────────────
load_dotenv()

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0.2
)

tools = [
    analyze_stock,
    get_fundamentals,
    compare_stocks,
    show_chart,
    show_comparison_chart,
    get_news,
    screen_stocks,
]

# ── ReAct Prompt ──────────────────────────────────────────────────────────────
react_template = """You are FinanceGPT, an expert AI financial analyst specialising in Indian stock markets (NSE/BSE).

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

STRICT FORMAT — follow this EXACTLY:
Question: the input question you must answer
Thought: reason step by step about which tool to use
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action (just the symbol or symbols, no extra text)
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: provide a clear, well-structured response with:
  • Key findings
  • Signal & confidence
  • Reasoning summary
  • Any caveats or risks

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(react_template)

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=6,
)

# ── Main Loop ──────────────────────────────────────────────────────────────────
HELP_TEXT = f"""
{C.BOLD}{C.CYAN}Available Commands:{C.RESET}
  {C.WHITE}Analyze a stock    {C.DIM}→  analyze TCS{C.RESET}
  {C.WHITE}Fundamentals       {C.DIM}→  fundamentals of HDFCBANK{C.RESET}
  {C.WHITE}Compare stocks     {C.DIM}→  compare TCS, INFY, WIPRO{C.RESET}
  {C.WHITE}Show chart         {C.DIM}→  show chart for RELIANCE{C.RESET}
  {C.WHITE}Comparison chart   {C.DIM}→  comparison chart TCS vs INFY{C.RESET}
  {C.WHITE}Latest news        {C.DIM}→  news for BAJFINANCE{C.RESET}
  {C.WHITE}Screen stocks      {C.DIM}→  screen TCS,INFY,WIPRO,HDFCBANK{C.RESET}
  {C.DIM}Type 'exit' to quit, 'help' for this menu{C.RESET}
"""

header("FINANCE AI AGENT  —  Powered by Groq + LLaMA 3.3-70b")
print(HELP_TEXT)

while True:
    try:
        query = input(f"{C.BOLD}{C.BLUE}FinanceGPT ▸ {C.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{C.DIM}Goodbye!{C.RESET}")
        break

    if not query:
        continue
    if query.lower() in ("exit", "quit", "q"):
        print(f"\n{C.DIM}Goodbye!{C.RESET}\n")
        break
    if query.lower() == "help":
        print(HELP_TEXT)
        continue

    print(f"\n{C.DIM}⏳  Processing — please wait...{C.RESET}\n")
    start = datetime.now()

    try:
        response = agent_executor.invoke({"input": query})
        elapsed  = int((datetime.now() - start).total_seconds() * 1000)
        publish_results(query, response["output"], elapsed)
    except Exception as e:
        print(f"\n{C.RED}{C.BOLD}Error:{C.RESET} {C.RED}{e}{C.RESET}\n")
