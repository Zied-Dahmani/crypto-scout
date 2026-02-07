"""
Crypto Scout - AI-powered viral trend and low-cap crypto discovery system.

This is the main entry point for running the crypto scout system.
"""

import asyncio
import argparse
from datetime import datetime, timezone

from config.settings import config
from agents import create_crypto_scout, run_trend_discovery, run_crypto_analysis
from utils.logger import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


async def run_single_scan():
    """Run a single crypto scout scan."""
    logger.info("=" * 60)
    logger.info("CRYPTO SCOUT - Single Scan Mode")
    logger.info("=" * 60)

    supervisor = create_crypto_scout()

    # Print workflow diagram
    print(supervisor.get_graph_diagram())

    # Run the scan
    result = await supervisor.run(thread_id=f"scan_{datetime.now(timezone.utc).timestamp()}")

    # Print results
    print("\n" + "=" * 60)
    print("SCAN RESULTS")
    print("=" * 60)

    for msg in result.get("messages", []):
        if hasattr(msg, "content"):
            print(msg.content)
            print("-" * 40)

    return result


async def run_continuous(interval_minutes: int = 5, max_runs: int = None):
    """Run continuous scanning."""
    logger.info("=" * 60)
    logger.info(f"CRYPTO SCOUT - Continuous Mode (every {interval_minutes} min)")
    logger.info("=" * 60)

    supervisor = create_crypto_scout()
    run_count = 0

    while max_runs is None or run_count < max_runs:
        run_count += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting scan #{run_count} at {datetime.now(timezone.utc)}")
        logger.info("=" * 60)

        try:
            await supervisor.run(thread_id=f"continuous_{run_count}")
        except Exception as e:
            logger.error(f"Scan #{run_count} failed: {e}")

        if max_runs is None or run_count < max_runs:
            logger.info(f"Waiting {interval_minutes} minutes until next scan...")
            await asyncio.sleep(interval_minutes * 60)

    logger.info(f"Completed {run_count} scans")


async def run_trend_only():
    """Run only the trend discovery agent."""
    logger.info("=" * 60)
    logger.info("CRYPTO SCOUT - Trend Discovery Only")
    logger.info("=" * 60)

    result = await run_trend_discovery()

    print("\n" + "=" * 60)
    print("TREND DISCOVERY RESULTS")
    print("=" * 60)

    for msg in result.get("messages", []):
        if hasattr(msg, "content"):
            print(msg.content)
            print("-" * 40)

    return result


async def run_crypto_only(trend_keywords: list[str] = None):
    """Run only the crypto analysis agent."""
    logger.info("=" * 60)
    logger.info("CRYPTO SCOUT - Crypto Analysis Only")
    logger.info("=" * 60)

    # Create mock trends if keywords provided
    trends = None
    if trend_keywords:
        trends = [
            {"keyword": kw, "virality": 0.7}
            for kw in trend_keywords
        ]

    result = await run_crypto_analysis(trends=trends)

    print("\n" + "=" * 60)
    print("CRYPTO ANALYSIS RESULTS")
    print("=" * 60)

    for msg in result.get("messages", []):
        if hasattr(msg, "content"):
            print(msg.content)
            print("-" * 40)

    return result


async def interactive_mode():
    """Run in interactive mode."""
    logger.info("=" * 60)
    logger.info("CRYPTO SCOUT - Interactive Mode")
    logger.info("=" * 60)

    print("""
Welcome to Crypto Scout Interactive Mode!

Commands:
  scan     - Run a full scan (trends + crypto analysis)
  trends   - Discover current trends only
  crypto   - Analyze cryptos only
  crypto <keyword> - Analyze cryptos for a specific trend
  diagram  - Show system diagram
  help     - Show this help
  exit     - Exit

""")

    supervisor = create_crypto_scout()

    while True:
        try:
            user_input = input("\n🔍 crypto-scout> ").strip().lower()

            if not user_input:
                continue

            if user_input == "exit":
                print("Goodbye!")
                break

            elif user_input == "help":
                print("Commands: scan, trends, crypto, crypto <keyword>, diagram, exit")

            elif user_input == "diagram":
                print(supervisor.get_graph_diagram())

            elif user_input == "scan":
                print("\nStarting full scan...")
                await run_single_scan()

            elif user_input == "trends":
                print("\nDiscovering trends...")
                await run_trend_only()

            elif user_input.startswith("crypto"):
                parts = user_input.split(maxsplit=1)
                keywords = [parts[1]] if len(parts) > 1 else None
                print(f"\nAnalyzing cryptos{f' for: {keywords}' if keywords else ''}...")
                await run_crypto_only(keywords)

            else:
                print(f"Unknown command: {user_input}. Type 'help' for commands.")

        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Crypto Scout - AI-powered viral trend and crypto discovery"
    )
    parser.add_argument(
        "mode",
        choices=["scan", "continuous", "trends", "crypto", "interactive"],
        default="scan",
        nargs="?",
        help="Run mode (default: scan)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval in minutes for continuous mode (default: 5)"
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Maximum runs for continuous mode (default: unlimited)"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        nargs="+",
        help="Keywords for crypto mode"
    )

    args = parser.parse_args()

    # Validate configuration
    if not config.llm.openai_api_key and not config.llm.anthropic_api_key:
        print("⚠️  WARNING: No LLM API key configured!")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
        print("The system will use mock data for demonstration.\n")

    # Run appropriate mode
    if args.mode == "scan":
        asyncio.run(run_single_scan())
    elif args.mode == "continuous":
        asyncio.run(run_continuous(args.interval, args.max_runs))
    elif args.mode == "trends":
        asyncio.run(run_trend_only())
    elif args.mode == "crypto":
        asyncio.run(run_crypto_only(args.keywords))
    elif args.mode == "interactive":
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
