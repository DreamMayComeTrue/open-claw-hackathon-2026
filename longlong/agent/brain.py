"""
龙龙's Brain — Groq fast + Claude tool calling
Streams response so TTS starts speaking before full reply is generated.
"""

import anthropic
import os
import re
from dotenv import load_dotenv
from tools import calendar_tools, browser_tools, email_tools, file_tools, system_tools, computer_tools
from utils.display import print_status

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """
You are 小龙小龙 (Xiǎo Lóng Xiǎo Lóng), a smart bilingual AI voice assistant. Nickname: 龙龙.
Built for Open Claw Hackathon 2026.

LANGUAGE RULE:
- User speaks Chinese → reply in Chinese
- User speaks English → reply in English
- Max 2-3 short sentences per reply. This is voice — be concise and natural.
- No markdown, no bullets, no emojis. Sound like a friend talking.
- You are 龙龙, never 小宝.

TOOLS available: Google Calendar, Gmail, browser, files, system apps, mouse/keyboard control, screen vision.
Use tools when user asks you to DO something. For chat/questions just reply directly.
"""

ALL_TOOLS = (
    calendar_tools.DEFINITIONS
    + browser_tools.DEFINITIONS
    + email_tools.DEFINITIONS
    + file_tools.DEFINITIONS
    + system_tools.DEFINITIONS
    + computer_tools.DEFINITIONS
)

TOOL_HANDLERS = {
    **calendar_tools.HANDLERS,
    **browser_tools.HANDLERS,
    **email_tools.HANDLERS,
    **file_tools.HANDLERS,
    **system_tools.HANDLERS,
    **computer_tools.HANDLERS,
}

TOOL_KEYWORDS = [
    "calendar","event","meeting","schedule","remind","appointment",
    "日历","会议","日程","提醒","创建","删除",
    "email","mail","send","邮件","发送",
    "open","close","search","youtube","google","website","browser",
    "打开","关闭","搜索","网站",
    "read","file","folder","path","读取","文件",
    "volume","screenshot","app","notepad","spotify","powershell","chrome","edge",
    "音量","截图","打开应用",
    "click","type","press","scroll","screen","mouse","keyboard",
    "what.*see","describe.*screen","find.*button","shortcut",
    "看屏幕","点击","输入","按键",
]


def _needs_tools(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in TOOL_KEYWORDS)


class XiaoBaoBrain:
    def __init__(self):
        self._groq = None
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self._groq = Groq(api_key=GROQ_API_KEY)
                print_status("Groq ready ✅", "green")
            except Exception as e:
                print_status(f"Groq init failed: {e}", "yellow")

        self._claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history = []
        self.last_language = "en"

    async def process(self, user_input: str) -> str:
        self.last_language = self._detect_lang(user_input)
        self.history.append({"role": "user", "content": user_input})

        if _needs_tools(user_input):
            print_status("→ Claude Haiku (tools)", "yellow")
            response = await self._claude_process(user_input)
        elif self._groq:
            print_status("→ Groq (fast)", "yellow")
            response = self._groq_stream(user_input)
        else:
            response = await self._claude_process(user_input)

        self.history.append({"role": "assistant", "content": response})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        return response

    def _groq_stream(self, user_input: str) -> str:
        """Groq streaming — collects full response fast."""
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += self.history[-6:]
            stream = self._groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=120,
                temperature=0.7,
                stream=True,
            )
            full = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full += delta
            return full.strip()
        except Exception as e:
            print_status(f"Groq failed: {e} — using Claude", "yellow")
            import asyncio
            loop = asyncio.new_event_loop()
            r = loop.run_until_complete(self._claude_process(user_input))
            loop.close()
            return r

    async def _claude_process(self, user_input: str) -> str:
        messages = self.history.copy()
        while True:
            response = self._claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                tools=ALL_TOOLS,
                messages=messages,
            )
            text_parts, tool_calls = [], []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            if not tool_calls:
                return " ".join(text_parts).strip()

            tool_results = []
            for tc in tool_calls:
                print_status(f"Tool: {tc.name}", "yellow")
                result = await self._run_tool(tc.name, tc.input)
                print_status(f"  → {result[:80]}", "blue")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": str(result),
                })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    async def _run_tool(self, name: str, inputs: dict) -> str:
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return f"Tool '{name}' not found"
        try:
            result = handler(**inputs)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as e:
            return f"Error: {e}"

    def _detect_lang(self, text: str) -> str:
        cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        return "zh" if cjk > len(text) * 0.2 else "en"