"""Crypto opportunity detection pipeline — entry point.

Usage:
    python main.py                        # run once
    python main.py --schedule             # run every 30 min (default)
    python main.py --schedule --interval 60  # run every 60 min
    python main.py --diagram              # print pipeline graph and exit
"""

import argparse
import time

from pipeline.graph import build_pipeline
from pipeline.state import PipelineState
from services.discord import send_alerts
from utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

_VERDICT_ICON = {"BUY": "🟢", "WATCH": "🟡", "SKIP": "🔴"}


# ── Display ───────────────────────────────────────────────────────────────────

def _print_results(state: PipelineState) -> None:
    print("\n" + "=" * 62)
    print("  CRYPTO OPPORTUNITY DETECTION — RESULTS")
    print("=" * 62)
    print(f"  Trends detected  : {len(state.get('raw_trends', []))}")
    print(f"  Trends validated : {len(state.get('validated_trends', []))}")
    print(f"  Tokens found     : {len(state.get('token_matches', []))}")
    print(f"  Opportunities    : {len(state.get('opportunities', []))}")

    errors = state.get("errors", [])
    if errors:
        print("\n  Errors:")
        for e in errors:
            print(f"    - {e}")

    opportunities = state.get("opportunities", [])
    if not opportunities:
        print("\n  No opportunities met the scoring threshold.\n")
        return

    print("\n" + "-" * 62)
    print("  TOP OPPORTUNITIES")
    print("-" * 62)

    for i, opp in enumerate(opportunities, 1):
        icon = _VERDICT_ICON.get(opp["verdict"], "")
        print(f"\n  #{i} {icon} [{opp['verdict']}] {opp['symbol']} — {opp['name']}")
        print(f"      Trend          : {opp['trend_keyword']}")
        print(
            f"      Score          : {opp['score']:.3f}  "
            f"(trend={opp['trend_momentum']:.2f}, "
            f"market={opp['market_quality']:.2f}, "
            f"smart={opp['smart_money_score']:.2f})"
        )
        print(f"      Market cap     : ${opp['market_cap']:>12,.0f}")
        print(f"      Volume 24h     : ${opp['volume_24h']:>12,.0f}")
        print(f"      Price change   : {opp['price_change_24h']:+.1f}%")
        print(f"      Price          : ${opp['current_price']:.8f}")

    print()


# ── Pipeline run ──────────────────────────────────────────────────────────────

def run() -> None:
    logger.info("Starting crypto opportunity detection pipeline")
    pipeline = build_pipeline()

    initial: PipelineState = {
        "raw_trends": [],
        "validated_trends": [],
        "token_matches": [],
        "market_data": [],
        "wallet_analyses": [],
        "opportunities": [],
        "errors": [],
    }

    final_state = pipeline.invoke(initial)
    _print_results(final_state)

    # Send Discord alerts for BUY / WATCH signals
    send_alerts(final_state.get("opportunities", []))


# ── Scheduler ─────────────────────────────────────────────────────────────────

def run_scheduled(interval_minutes: int) -> None:
    import schedule

    logger.info(f"Scheduler started — running every {interval_minutes} minutes")
    run()  # run immediately on start

    schedule.every(interval_minutes).minutes.do(run)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crypto Opportunity Detection Pipeline")
    parser.add_argument("--schedule",  action="store_true",  help="Run on a repeating schedule")
    parser.add_argument("--interval",  type=int, default=30, help="Schedule interval in minutes (default: 30)")
    parser.add_argument("--diagram",   action="store_true",  help="Print ASCII pipeline diagram and exit")
    args = parser.parse_args()

    if args.diagram:
        pipeline = build_pipeline()
        print(pipeline.get_graph().draw_ascii())
    elif args.schedule:
        run_scheduled(args.interval)
    else:
        run()
