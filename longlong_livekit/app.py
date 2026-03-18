"""
龙龙 Desktop App — PyQt5 + WebEngine
Run: python app.py
No browser popups, mic pre-granted, looks like a real app.
"""

import os, sys, subprocess, time
from dotenv import load_dotenv

load_dotenv()

# ── Generate LiveKit token ────────────────────────────────────────────────────
def generate_token():
    URL    = os.getenv("LIVEKIT_URL", "")
    KEY    = os.getenv("LIVEKIT_API_KEY", "")
    SECRET = os.getenv("LIVEKIT_API_SECRET", "")

    if not all([URL, KEY, SECRET]):
        print("❌ Missing LIVEKIT_URL, LIVEKIT_API_KEY, or LIVEKIT_API_SECRET in .env")
        sys.exit(1)

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
    return URL, KEY, SECRET, token


# ── Dispatch agent to room ────────────────────────────────────────────────────
def dispatch_agent(URL, KEY, SECRET):
    try:
        from livekit.api import (
            LiveKitAPI,
            CreateAgentDispatchRequest,
            DeleteAgentDispatchRequest,
            ListAgentDispatchRequest,
        )
        import asyncio

        async def _dispatch():
            async with LiveKitAPI(URL, KEY, SECRET) as api:
                # Clear old dispatches first to avoid duplicate agents
                try:
                    existing = await api.agent_dispatch.list_dispatch(
                        ListAgentDispatchRequest(room="longlong-room")
                    )
                    for d in existing.agent_dispatches:
                        await api.agent_dispatch.delete_dispatch(
                            DeleteAgentDispatchRequest(
                                dispatch_id=d.id,
                                room="longlong-room"
                            )
                        )
                        print("🗑️  Removed old dispatch")
                except Exception:
                    pass

                # Fresh dispatch
                await api.agent_dispatch.create_dispatch(
                    CreateAgentDispatchRequest(
                        agent_name="longlong",
                        room="longlong-room",
                    )
                )

        asyncio.run(_dispatch())
        print("✅ Agent dispatched")
    except Exception as e:
        print(f"⚠️  Dispatch warning: {e}")


# ── Build HTML with injected credentials ─────────────────────────────────────
def build_html(URL, KEY, SECRET, token):
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "frontend.html"), "r", encoding="utf-8") as f:
        html = f.read()

    # Remove the permission overlay — not needed in desktop app
    html = html.replace(
        "document.mediaDevices.getUserMedia",
        "navigator.mediaDevices.getUserMedia"
    )
    html = html.replace(
        "</body>",
        """<script>
        window.addEventListener('load', () => {
            setTimeout(() => { autoConnect(); }, 800);
        });
        </script></body>"""
    )

    html = html.replace("LIVEKIT_URL_PLACEHOLDER", URL)
    html = html.replace("LIVEKIT_KEY_PLACEHOLDER", KEY)
    html = html.replace("LIVEKIT_SECRET_PLACEHOLDER", SECRET)
    html = html.replace("TOKEN_PLACEHOLDER", token)
    return html


# ── PyQt5 Desktop Window ──────────────────────────────────────────────────────
def run_desktop_app(html_content):
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
        from PyQt5.QtCore import QUrl
    except ImportError:
        print("❌ PyQt5 not installed. Run: pip install PyQt5 PyQtWebEngine")
        sys.exit(1)

    # Must set before QApplication
    #
    # Added dark UI flags for Windows 11 overlay scrollbars / widgets:
    # - forces Chromium UI (scrollbars, form controls) into dark mode
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--use-fake-ui-for-media-stream "                 # auto-grant mic/camera — NO popup
        "--disable-features=WebRtcHideLocalIpsWithMdns "
        "--allow-running-insecure-content "
        "--force-dark-mode "
        "--enable-features=WebUIDarkMode "
        "--blink-settings=preferredColorScheme=0 "         # 0=dark, 1=light
    )


    app = QApplication(sys.argv)
    app.setApplicationName("LongLong AI Agent")

    window = QMainWindow()
    window.setWindowTitle("龙龙 · LongLong — Open Claw Hackathon 2026")
    window.setMinimumSize(900, 650)
    window.resize(1200, 800)
    window.setStyleSheet("QMainWindow { background: #060608; }")

    view = QWebEngineView()
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
    settings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, False)

    # Grant all feature permissions (belt AND suspenders)
    page = view.page()
    page.featurePermissionRequested.connect(
        lambda origin, feature: page.setFeaturePermission(
            origin, feature, QWebEnginePage.PermissionGrantedByUser
        )
    )

    view.setHtml(html_content, QUrl("https://localhost"))
    window.setCentralWidget(view)
    window.showMaximized()   # start maximized — fills the screen nicely


    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        # Clean exit if you press Ctrl+C in terminal
        try:
            window.close()
        except Exception:
            pass
        return


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🐉 Starting LongLong Desktop Agent...")

    # Generate credentials
    URL, KEY, SECRET, token = generate_token()
    print("✅ Token ready")

    # Start the LiveKit agent in background
    # NOTE: if you previously had watcher/IPC issues on Windows, you can remove "dev".
    base = os.path.dirname(os.path.abspath(__file__))
    agent_proc = subprocess.Popen(
        [sys.executable, os.path.join(base, "agent.py"), "dev"],
        cwd=base,
    )
    print(f"🤖 Agent started (PID: {agent_proc.pid})")

    # Dispatch agent to room
    print("📡 Dispatching agent to room...")
    dispatch_agent(URL, KEY, SECRET)

    # Wait for agent to be ready
    print("⏳ Waiting for agent (3s)...")
    time.sleep(3)

    # Build HTML
    html = build_html(URL, KEY, SECRET, token)

    # Launch desktop app
    print("🖥️  Opening desktop window...")
    try:
        run_desktop_app(html)
    except Exception as e:
        print(f"❌ Desktop app error: {e}")
        print("   Falling back to browser...")
        import webbrowser
        out = os.path.join(base, "_longlong_ui.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(f"file:///{out.replace(os.sep, '/')}")
        try:
            agent_proc.wait()
        except KeyboardInterrupt:
            agent_proc.terminate()
    finally:
        agent_proc.terminate()