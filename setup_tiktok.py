"""One-time TikTok session setup.

Run this locally whenever your TikTok session expires:
    python setup_tiktok.py

It will:
1. Open a visible browser — log into TikTok (use Continue with Google)
2. Save session to .tiktok_session/state.json
3. Upload it as TIKTOK_SESSION GitHub secret automatically
"""

import asyncio
import base64
import json
import subprocess
import sys
from pathlib import Path

_SESSION_DIR = Path(__file__).parent / ".tiktok_session"
_SESSION_FILE = _SESSION_DIR / "state.json"
_REPO = "Zied-Dahmani/crypto-scout"


async def _browser_login() -> bool:
    from playwright.async_api import async_playwright

    print("\n" + "=" * 60)
    print("  TIKTOK SESSION SETUP")
    print("=" * 60)
    print("A browser window will open.")
    print("→ Click 'Log in' → 'Continue with Google'")
    print("→ Sign in with: cryptoscout04 / cryptoscout09")
    print("→ Once on the TikTok homepage, come back here")
    print("=" * 60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login", wait_until="networkidle", timeout=30_000)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "Press ENTER after you are logged in... ")

        # Verify actually logged in
        current_url = page.url
        if "login" in current_url:
            print("❌ Still on login page — please log in first then press ENTER")
            await loop.run_in_executor(None, input, "Press ENTER again... ")

        _SESSION_DIR.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(_SESSION_FILE))
        await browser.close()

    print(f"✅ Session saved to {_SESSION_FILE}")
    return True


def _upload_to_github() -> bool:
    """Base64-encode session and upload as GitHub secret via gh CLI."""
    if not _SESSION_FILE.exists():
        print("❌ Session file not found")
        return False

    session_b64 = base64.b64encode(_SESSION_FILE.read_bytes()).decode()

    result = subprocess.run(
        ["gh", "secret", "set", "TIKTOK_SESSION",
         "--body", session_b64,
         "--repo", _REPO],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"❌ Failed to upload secret: {result.stderr}")
        print("Make sure 'gh' CLI is installed and you're logged in (gh auth login)")
        return False

    print("✅ Session uploaded to GitHub secrets as TIKTOK_SESSION")
    return True


async def main():
    ok = await _browser_login()
    if not ok:
        sys.exit(1)

    ok = _upload_to_github()
    if not ok:
        print("\nManual alternative: copy the content of .tiktok_session/state.json,")
        print("base64-encode it, and add as TIKTOK_SESSION in GitHub secrets.")
        sys.exit(1)

    print("\n✅ All done! TikTok is now set up on GitHub Actions.")
    print("Session lasts ~30-60 days. Re-run this script when it expires.")


if __name__ == "__main__":
    asyncio.run(main())
