"""TikTok trend scraper — intercepts XHR calls via Playwright.

Playwright visits tiktok.com/trending, intercepts the internal API response
that carries trending video data, and parses hashtags + view counts from it.
No TikTokApi library dependency — no 10201 / session errors.

Falls back to mock data on any failure so the pipeline always completes.
"""

import asyncio
import json
import re
from collections import defaultdict

from utils.logger import get_logger

logger = get_logger(__name__)

_MIN_VIEWS = 500_000
_SAMPLE_COUNT = 50
_TOP_N = 10


# ── Playwright scraper ────────────────────────────────────────────────────────

async def _scrape_trending() -> list[dict]:
    """Visit TikTok trending/explore page and extract hashtag data from embedded JSON."""
    from playwright.async_api import async_playwright

    logger.info("tiktok: launching Playwright to scrape trending")

    captured_videos: list[dict] = []
    captured_hashtags: list[dict] = []  # trending hashtag objects from discover page

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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

        # Intercept JSON API responses with video / hashtag data
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
                # Video lists
                for key in ("aweme_list", "item_list"):
                    items = data.get(key) or []
                    if items:
                        logger.info(f"tiktok: intercepted {len(items)} videos from {url[:80]}")
                        captured_videos.extend(items)
                # Hashtag / challenge lists
                for key in ("challenge_list", "hashtag_list", "challenge_info_list"):
                    items = data.get(key) or []
                    if items:
                        logger.info(f"tiktok: intercepted {len(items)} hashtags from {url[:80]}")
                        captured_hashtags.extend(items)
            except Exception:
                pass

        page.on("response", handle_response)

        urls_to_try = [
            "https://www.tiktok.com/trending",
            "https://www.tiktok.com/explore",
            "https://www.tiktok.com/tag/trending",
        ]

        for url in urls_to_try:
            try:
                await page.goto(url, wait_until="networkidle", timeout=35_000)
                await page.wait_for_timeout(4_000)
                await page.evaluate("window.scrollBy(0, 1500)")
                await page.wait_for_timeout(2_000)
                if captured_videos or captured_hashtags:
                    break
            except Exception as e:
                logger.debug(f"tiktok: {url} load error ({e})")

        # Also try to extract embedded __NEXT_DATA__ / SIGI_STATE JSON
        if not captured_videos and not captured_hashtags:
            try:
                html = await page.content()
                for pattern in [
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});',
                    r'<script id="SIGI_STATE"[^>]*>(.*?)</script>',
                    r'window\[[\'"__INITIAL_STATE__[\'\"]\]\s*=\s*(\{.*?\});',
                ]:
                    m = re.search(pattern, html, re.DOTALL)
                    if m:
                        try:
                            data = json.loads(m.group(1))
                            # Walk the JSON tree looking for video arrays
                            _extract_deep(data, captured_videos)
                            if captured_videos:
                                logger.info(f"tiktok: extracted {len(captured_videos)} items from page JSON")
                                break
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"tiktok: page content extraction failed ({e})")

        await browser.close()

    if not captured_videos and not captured_hashtags:
        logger.warning("tiktok: no data captured from any source")
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
        logger.info(f"tiktok: {len(unique)} unique videos captured")
        result = _parse_videos(unique[:_SAMPLE_COUNT])
        if result:
            return result

    # Fallback: build trends from raw hashtag objects
    if captured_hashtags:
        return _parse_hashtag_objects(captured_hashtags)

    return []


def _extract_deep(obj, out: list, depth: int = 0) -> None:
    """Recursively walk a JSON tree and collect objects that look like TikTok videos."""
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
    """Build trend signals from TikTok challenge/hashtag objects."""
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
    """Extract hashtag trends from raw TikTok video objects."""
    keyword_stats: dict[str, dict] = defaultdict(
        lambda: {"views": 0, "video_count": 0, "hashtags": set()}
    )

    for video in videos:
        # Support different response schemas
        stats = video.get("statistics") or video.get("stats") or {}
        views = (
            stats.get("play_count")
            or stats.get("playCount")
            or stats.get("video_play_count")
            or 0
        )

        desc = (
            video.get("desc")
            or (video.get("video") or {}).get("description", "")
            or ""
        )

        raw_tags = re.findall(r"#(\w+)", desc)

        # Also pull from challenges / textExtra arrays
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
        trends.append(
            {
                "keyword": kw,
                "hashtags": sorted(stats["hashtags"])[:5],
                "views": stats["views"],
                "growth_rate": growth_rate,
                "source": "tiktok",
            }
        )

    trends.sort(key=lambda x: x["views"], reverse=True)
    return trends[:_TOP_N]


# ── Public entry point ────────────────────────────────────────────────────────

def fetch_tiktok_trends() -> list[dict]:
    """Fetch trending topics from TikTok. Falls back to mock on any failure."""
    try:
        logger.info("tiktok: starting Playwright scraper")
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
        {"keyword": "moo deng",      "hashtags": ["#moodeng", "#babyhippo", "#thailand"],  "views": 620_000_000,   "growth_rate": 345.0, "source": "tiktok_mock"},
        {"keyword": "chill guy",     "hashtags": ["#chillguy", "#relatable", "#meme"],      "views": 980_000_000,   "growth_rate": 412.0, "source": "tiktok_mock"},
        {"keyword": "skibidi",       "hashtags": ["#skibidi", "#genz", "#toilet"],           "views": 1_400_000_000, "growth_rate": 88.0,  "source": "tiktok_mock"},
        {"keyword": "hawk tuah",     "hashtags": ["#hawktuah", "#viral", "#meme"],           "views": 780_000_000,   "growth_rate": 290.0, "source": "tiktok_mock"},
        {"keyword": "trump",         "hashtags": ["#trump", "#politics", "#usa"],            "views": 2_100_000_000, "growth_rate": 520.0, "source": "tiktok_mock"},
        {"keyword": "pepe",          "hashtags": ["#pepe", "#crypto", "#meme"],              "views": 450_000_000,   "growth_rate": 180.0, "source": "tiktok_mock"},
        {"keyword": "dogwifhat",     "hashtags": ["#dogwifhat", "#wif", "#solana"],          "views": 320_000_000,   "growth_rate": 210.0, "source": "tiktok_mock"},
        {"keyword": "capybara",      "hashtags": ["#capybara", "#animal", "#cute"],          "views": 560_000_000,   "growth_rate": 95.0,  "source": "tiktok_mock"},
        {"keyword": "griddy",        "hashtags": ["#griddy", "#nfl", "#dance"],              "views": 290_000_000,   "growth_rate": 155.0, "source": "tiktok_mock"},
        {"keyword": "pudgy penguin", "hashtags": ["#pudgypenguins", "#nft", "#pengu"],       "views": 180_000_000,   "growth_rate": 230.0, "source": "tiktok_mock"},
    ]
