"""
launch.py — starts agent + opens frontend
"""
import os, subprocess, sys, time, webbrowser
from dotenv import load_dotenv

load_dotenv()

URL    = os.getenv("LIVEKIT_URL", "")
KEY    = os.getenv("LIVEKIT_API_KEY", "")
SECRET = os.getenv("LIVEKIT_API_SECRET", "")

if not all([URL, KEY, SECRET]):
    print("❌ Missing LiveKit credentials in .env")
    sys.exit(1)

try:
    from livekit.api import AccessToken, VideoGrants
    token = (
        AccessToken(KEY, SECRET)
        .with_identity("user-demo")
        .with_name("Demo User")
        .with_grants(VideoGrants(
            room_join=True,
            room="longlong-room",
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
        .to_jwt()
    )
    print(f"✅ Token generated")
except Exception as e:
    print(f"❌ pip install livekit-api → {e}")
    sys.exit(1)

# Also create a dispatch token so LiveKit sends the agent to the room
try:
    from livekit.api import LiveKitAPI, CreateAgentDispatchRequest
    import asyncio

    async def dispatch_agent():
        async with LiveKitAPI(URL, KEY, SECRET) as api:
            dispatch = await api.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    agent_name="longlong",
                    room="longlong-room",
                )
            )
            print(f"✅ Agent dispatched: {dispatch.id}")

    asyncio.run(dispatch_agent())
except Exception as e:
    print(f"⚠️  Agent dispatch failed (will try auto-dispatch): {e}")

# Inject into HTML
base = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base, "frontend.html"), "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("LIVEKIT_URL_PLACEHOLDER", URL)
html = html.replace("LIVEKIT_KEY_PLACEHOLDER", KEY)
html = html.replace("LIVEKIT_SECRET_PLACEHOLDER", SECRET)
html = html.replace("TOKEN_PLACEHOLDER", token)

out = os.path.join(base, "_longlong_ui.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print("🐉 Starting LongLong agent...")
agent = subprocess.Popen(
    [sys.executable, os.path.join(base, "agent.py"), "dev"],
    cwd=base,
)

print("⏳ Waiting for agent (5s)...")
time.sleep(5)

webbrowser.open(f"file:///{out.replace(os.sep, '/')}")
print("🌐 Frontend opened!")
print(f"✅ Agent PID: {agent.pid} — Press Ctrl+C to stop\n")

try:
    agent.wait()
except KeyboardInterrupt:
    print("\n👋 Shutting down...")
    agent.terminate()