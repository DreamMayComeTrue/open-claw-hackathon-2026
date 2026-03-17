"""
龙龙's Brain — Groq for fast responses, Claude for tool calling
Groq (llama-3.3-70b) handles simple conversation at ~200ms
Claude handles calendar, email, browser, file, system tools
"""

import anthropic
import os
from dotenv import load_dotenv
from tools import calendar_tools, browser_tools, email_tools, file_tools, system_tools
from utils.display import print_status

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """
You are 小龙小龙 (Xiǎo Lóng Xiǎo Lóng), a friendly bilingual AI voice assistant.
Your nickname is 龙龙. Built for Open Claw Hackathon 2026.

LANGUAGE RULE:
- User speaks Chinese → reply in Chinese
- User speaks English → reply in English
- Keep replies SHORT — max 2 sentences. This is voice, not text.
- No markdown, no bullet points, no emojis.
- Sound warm and natural like a friend.
- You are 龙龙, never 小宝 or any other name.

TOOL USE:
You have access to: Google Calendar, browser, email, file reader, system controls.
Use tools when the user asks you to DO something. 
For simple questions or chat, just reply directly — no tools needed.
"""

ALL_TOOLS = (
    calendar_tools.DEFINITIONS
    + browser_tools.DEFINITIONS
    + email_tools.DEFINITIONS
    + file_tools.DEFINITIONS
    + system_tools.DEFINITIONS
)

TOOL_HANDLERS = {
    **calendar_tools.HANDLERS,
    **browser_tools.HANDLERS,
    **email_tools.HANDLERS,
    **file_tools.HANDLERS,
    **system_tools.HANDLERS,
}

# Keywords that suggest tool use is needed
TOOL_KEYWORDS = [
    # Calendar
    "calendar", "event", "meeting", "schedule", "remind", "appointment",
    "日历", "会议", "日程", "提醒", "创建", "删除",
    # Browser
    "open", "search", "youtube", "google", "website", "browser",
    "打开", "搜索", "网站",
    # Email
    "email", "mail", "send", "邮件", "发送",
    # File
    "read", "file", "folder", "path", "读取", "文件",
    # System
    "volume", "screenshot", "app", "notepad", "spotify",
    "音量", "截图", "打开应用",
]


def _needs_tools(text: str) -> bool:
    """Quick check if the command likely needs a tool."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in TOOL_KEYWORDS)


class XiaoBaoBrain:
    def __init__(self):
        # Groq client for fast replies
        self._groq_client = None
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=GROQ_API_KEY)
                print_status("Groq client ready ✅ (fast mode)", "green")
            except ImportError:
                print_status("groq package not installed — pip install groq", "yellow")
            except Exception as e:
                print_status(f"Groq init failed: {e}", "yellow")

        # Claude client for tool calling
        self._claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        self.conversation_history = []
        self.last_language = "en"

    async def process(self, user_input: str) -> str:
        self.last_language = self._detect_language(user_input)
        self.conversation_history.append({"role": "user", "content": user_input})

        # Route: tool needed → Claude, simple chat → Groq
        if _needs_tools(user_input):
            print_status("→ Claude (tool use)", "yellow")
            response = await self._claude_process(user_input)
        elif self._groq_client:
            print_status("→ Groq (fast reply)", "yellow")
            response = self._groq_process(user_input)
        else:
            print_status("→ Claude (no Groq key)", "yellow")
            response = await self._claude_process(user_input)

        self.conversation_history.append({"role": "assistant", "content": response})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        return response

    def _groq_process(self, user_input: str) -> str:
        """Ultra-fast reply via Groq — no tools, just conversation."""
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            # Include last 6 turns for context
            messages += self.conversation_history[-6:]

            resp = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=150,        # short voice replies only
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print_status(f"Groq failed ({e}) — falling back to Claude", "yellow")
            import asyncio
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._claude_process(user_input))
            loop.close()
            return result

    async def _claude_process(self, user_input: str) -> str:
        """Claude with full tool calling for actions."""
        messages = self.conversation_history.copy()

        while True:
            response = self._claude_client.messages.create(
                model="claude-haiku-4-5-20251001",   # fastest Claude model
                max_tokens=512,
                system=SYSTEM_PROMPT,
                tools=ALL_TOOLS,
                messages=messages,
            )

            text_parts = []
            tool_calls = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if not tool_calls:
                return " ".join(text_parts).strip()

            # Execute tools
            tool_results = []
            for tc in tool_calls:
                print_status(f"🔧 {tc.name}", "yellow")
                result = await self._execute_tool(tc.name, tc.input)
                print_status(f"   → {result}", "blue")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": str(result),
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' not found."
        try:
            result = handler(**tool_input)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as e:
            return f"Tool error: {e}"

    def _detect_language(self, text: str) -> str:
        cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        return "zh" if cjk > len(text) * 0.2 else "en"