"""TikTok trend scraper — intercepts XHR calls via Playwright.

Session loading priority:
  1. TIKTOK_SESSION env var (base64-encoded — used on GitHub Actions)
  2. .tiktok_session/state.json (local file — used when running locally)
  3. One-time visible-browser login (first local run only)

When session expires → sends Discord alert and falls back to mock.
Falls back to mock on any failure so the pipeline always completes.
"""

import asyncio
import base64
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_MIN_VIEWS = 500_000
_SAMPLE_COUNT = 50
_TOP_N = 10
_SESSION_DIR = Path(__file__).parent.parent / ".tiktok_session"
_SESSION_FILE = _SESSION_DIR / "state.json"


# ── Session management ────────────────────────────────────────────────────────

def _load_session_from_env() -> bool:
    """Decode TIKTOK_SESSION env var and write to local session file."""
    session_b64 = os.environ.get("TIKTOK_SESSION", "")
    if not session_b64:
        return False
    try:
        session_data = base64.b64decode(session_b64)
        _SESSION_DIR.mkdir(parents=True, exist_ok=True)
        _SESSION_FILE.write_bytes(session_data)
        logger.info("tiktok: session loaded from TIKTOK_SESSION env var")
        return True
    except Exception as e:
        logger.warning(f"tiktok: failed to decode TIKTOK_SESSION ({e})")
        return False


def _session_exists() -> bool:
    return _SESSION_FILE.exists() and _SESSION_FILE.stat().st_size > 0


def _clear_session():
    shutil.rmtree(_SESSION_DIR, ignore_errors=True)


async def _setup_session() -> bool:
    """Open a visible browser for one-time manual TikTok login, then save session."""
    from playwright.async_api import async_playwright

    logger.info("tiktok: no saved session — opening browser for one-time login")
    print("\n" + "=" * 60)
    print("  TIKTOK SETUP — One-time login required")
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

        _SESSION_DIR.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(_SESSION_FILE))
        await browser.close()

    logger.info("tiktok: session saved")
    return True


# ── Playwright scraper ────────────────────────────────────────────────────────

async def _scrape_trending() -> list[dict]:
    """Visit TikTok trending/explore page and extract hashtag data from embedded JSON."""
    from playwright.async_api import async_playwright

    # Priority: env var → local file → interactive setup
    if not _session_exists():
        _load_session_from_env() or await _setup_session()

    if not _session_exists():
        return []

    logger.info("tiktok: launching Playwright with saved session")

    captured_videos: list[dict] = []
    captured_hashtags: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state=str(_SESSION_FILE),
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        async def handle_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            if not any(k in url for k in [
                "recommend", "trending", "item_list", "aweme/v1",
                "discover", "explore", "challenge/list",
            ]):
                return
            try:
                body = await response.body()
                data = json.loads(body)
                for key in ("aweme_list", "item_list"):
                    items = data.get(key) or []
                    if items:
                        logger.info(f"tiktok: intercepted {len(items)} videos from {url[:80]}")
                        captured_videos.extend(items)
                for key in ("challenge_list", "hashtag_list", "challenge_info_list"):
                    items = data.get(key) or []
                    if items:
                        logger.info(f"tiktok: intercepted {len(items)} hashtags from {url[:80]}")
                        captured_hashtags.extend(items)
            except Exception:
                pass

        page.on("response", handle_response)

        for url in [
            "https://www.tiktok.com/trending",
            "https://www.tiktok.com/explore",
            "https://www.tiktok.com/tag/trending",
        ]:
            try:
                await page.goto(url, wait_until="networkidle", timeout=35_000)
                await page.wait_for_timeout(4_000)
                await page.evaluate("window.scrollBy(0, 1500)")
                await page.wait_for_timeout(2_000)
                if captured_videos or captured_hashtags:
                    break
            except Exception as e:
                logger.debug(f"tiktok: {url} load error ({e})")

        # Detect session expiry (redirected to login)
        if "login" in page.url:
            logger.warning("tiktok: session expired — clearing saved session")
            _clear_session()
            await browser.close()
            _notify_session_expired()
            return []

        # Fallback: extract from embedded page JSON
        if not captured_videos and not captured_hashtags:
            try:
                html = await page.content()
                for pattern in [
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    r'<script id="SIGI_STATE"[^>]*>(.*?)</script>',
                ]:
                    m = re.search(pattern, html, re.DOTALL)
                    if m:
                        try:
                            data = json.loads(m.group(1))
                            _extract_deep(data, captured_videos)
                            if captured_videos:
                                break
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"tiktok: page content extraction failed ({e})")

        # Refresh saved session
        try:
            await context.storage_state(path=str(_SESSION_FILE))
        except Exception:
            pass

        await browser.close()

    if not captured_videos and not captured_hashtags:
        logger.warning("tiktok: no data captured")
        return []

    if captured_videos:
        seen_ids: set = set()
        unique: list[dict] = []
        for item in captured_videos:
            vid_id = item.get("id") or item.get("aweme_id") or ""
            if vid_id and vid_id not in seen_ids:
                seen_ids.add(vid_id)
                unique.append(item)
            elif not vid_id:
                unique.append(item)
        result = _parse_videos(unique[:_SAMPLE_COUNT])
        if result:
            return result

    if captured_hashtags:
        return _parse_hashtag_objects(captured_hashtags)

    return []


# ── Session expiry notification ───────────────────────────────────────────────

def _notify_session_expired():
    """Send a Discord alert when TikTok session expires."""
    webhook_url = config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        return
    try:
        import requests
        requests.post(webhook_url, json={
            "embeds": [{
                "title": "⚠️ TikTok Session Expired",
                "description": (
                    "The TikTok session has expired. The bot is using **mock TikTok data** until refreshed.\n\n"
                    "**To fix (2 min):**\n"
                    "1. Open Chrome → go to **tiktok.com** → click **Log in with Google** → use `cryptoscout04@gmail.com`\n"
                    "2. Once logged in, open the **EditThisCookie** extension → click **Export**\n"
                    "3. Paste the exported cookies to the developer to upload the new session"
                ),
                "color": 0xFF6600,
            }]
        }, timeout=10)
    except Exception:
        pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_deep(obj, out: list, depth: int = 0) -> None:
    if depth > 8 or len(out) >= _SAMPLE_COUNT:
        return
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict) and ("desc" in item or "aweme_id" in item):
                out.append(item)
            else:
                _extract_deep(item, out, depth + 1)
    elif isinstance(obj, dict):
        for v in obj.values():
            _extract_deep(v, out, depth + 1)


def _parse_hashtag_objects(hashtags: list[dict]) -> list[dict]:
    trends = []
    for h in hashtags:
        info = h.get("challenge_info") or h.get("hashtag_info") or h
        title = (info.get("cha_name") or info.get("hashtag_name") or "").lower()
        views = int(info.get("view_count") or info.get("use_count") or 0)
        if not title or views < _MIN_VIEWS:
            continue
        growth_rate = round(min(views / 10_000_000 * 100, 999.0), 1)
        trends.append({
            "keyword": title,
            "hashtags": [f"#{title}"],
            "views": views,
            "growth_rate": growth_rate,
            "source": "tiktok",
        })
    trends.sort(key=lambda x: x["views"], reverse=True)
    return trends[:_TOP_N]


def _parse_videos(videos: list[dict]) -> list[dict]:
    keyword_stats: dict[str, dict] = defaultdict(
        lambda: {"views": 0, "video_count": 0, "hashtags": set()}
    )
    for video in videos:
        stats = video.get("statistics") or video.get("stats") or {}
        views = (
            stats.get("play_count")
            or stats.get("playCount")
            or stats.get("video_play_count")
            or 0
        )
        desc = video.get("desc") or (video.get("video") or {}).get("description", "") or ""
        raw_tags = re.findall(r"#(\w+)", desc)
        for ch in video.get("challenges") or video.get("textExtra") or []:
            tag = ch.get("title") or ch.get("hashtagName") or ""
            if tag:
                raw_tags.append(tag)
        for tag in raw_tags:
            kw = tag.lower()
            keyword_stats[kw]["views"] += views
            keyword_stats[kw]["video_count"] += 1
            keyword_stats[kw]["hashtags"].add(f"#{tag}")

    trends = []
    for kw, stats in keyword_stats.items():
        if stats["views"] < _MIN_VIEWS:
            continue
        avg_views = stats["views"] / max(stats["video_count"], 1)
        growth_rate = round(min(avg_views / 1_000_000 * 100, 999.0), 1)
        trends.append({
            "keyword": kw,
            "hashtags": sorted(stats["hashtags"])[:5],
            "views": stats["views"],
            "growth_rate": growth_rate,
            "source": "tiktok",
        })
    trends.sort(key=lambda x: x["views"], reverse=True)
    return trends[:_TOP_N]


# ── Public entry point ────────────────────────────────────────────────────────

def fetch_tiktok_trends() -> list[dict]:
    """Fetch trending topics from TikTok. Falls back to mock on any failure."""
    try:
        trends = asyncio.run(_scrape_trending())
        if trends:
            logger.info(f"tiktok: scraped {len(trends)} trend signals")
            return trends
        logger.warning("tiktok: scraper returned 0 results, falling back to mock")
    except Exception as e:
        logger.warning(f"tiktok: scraper failed ({e}), falling back to mock")

    return _mock_trends()


# ── Mock fallback ─────────────────────────────────────────────────────────────

def _mock_trends() -> list[dict]:
    return [
        {"keyword": "moo deng",      "hashtags": ["#moodeng", "#babyhippo"],      "views": 620_000_000,   "growth_rate": 345.0, "source": "tiktok_mock"},
        {"keyword": "chill guy",     "hashtags": ["#chillguy", "#meme"],           "views": 980_000_000,   "growth_rate": 412.0, "source": "tiktok_mock"},
        {"keyword": "skibidi",       "hashtags": ["#skibidi", "#genz"],             "views": 1_400_000_000, "growth_rate": 88.0,  "source": "tiktok_mock"},
        {"keyword": "hawk tuah",     "hashtags": ["#hawktuah", "#viral"],           "views": 780_000_000,   "growth_rate": 290.0, "source": "tiktok_mock"},
        {"keyword": "trump",         "hashtags": ["#trump", "#politics"],           "views": 2_100_000_000, "growth_rate": 520.0, "source": "tiktok_mock"},
        {"keyword": "pepe",          "hashtags": ["#pepe", "#crypto"],              "views": 450_000_000,   "growth_rate": 180.0, "source": "tiktok_mock"},
        {"keyword": "dogwifhat",     "hashtags": ["#dogwifhat", "#solana"],         "views": 320_000_000,   "growth_rate": 210.0, "source": "tiktok_mock"},
        {"keyword": "capybara",      "hashtags": ["#capybara", "#cute"],            "views": 560_000_000,   "growth_rate": 95.0,  "source": "tiktok_mock"},
        {"keyword": "griddy",        "hashtags": ["#griddy", "#nfl"],               "views": 290_000_000,   "growth_rate": 155.0, "source": "tiktok_mock"},
        {"keyword": "pudgy penguin", "hashtags": ["#pudgypenguins", "#pengu"],      "views": 180_000_000,   "growth_rate": 230.0, "source": "tiktok_mock"},
    ]
