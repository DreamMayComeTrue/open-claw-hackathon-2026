# utils/display.py

COLORS = {
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "blue":   "\033[94m",
    "cyan":   "\033[96m",
    "white":  "\033[97m",
    "reset":  "\033[0m",
}

def print_status(msg: str, color: str = "white"):
    c = COLORS.get(color, COLORS["white"])
    print(f"{c}{msg}{COLORS['reset']}")

def print_banner():
    banner = """
\033[96m
  ╔═══════════════════════════════════╗
  ║       龙龙  LONG LONG AGENT        ║
  ║   Bilingual Voice AI Agent 🐉     ║
  ║   Chinese + English | Hackathon   ║
  ╚═══════════════════════════════════╝
\033[0m"""
    print(banner)
