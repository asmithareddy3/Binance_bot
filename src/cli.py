# src/cli.py
import argparse
import json
import os
from dotenv import load_dotenv

from logger_setup import setup_logger
from basic_bot import BasicBot
from twap import TWAP

logger = setup_logger()

def load_config(path="config.json"):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    # fallback to env
    load_dotenv()
    return {
        "API_KEY": os.getenv("API_KEY"),
        "API_SECRET": os.getenv("API_SECRET"),
        "BASE_URL": os.getenv("BASE_URL", "https://testnet.binancefuture.com"),
        "RECV_WINDOW": int(os.getenv("RECV_WINDOW", 5000))
    }

def main():
    parser = argparse.ArgumentParser(description="Simplified Binance Futures Bot (Testnet)")
    sub = parser.add_subparsers(dest="command", required=True)

    # market
    p_market = sub.add_parser("market", help="Place a market order")
    p_market.add_argument("symbol")
    p_market.add_argument("side", choices=["BUY", "SELL"])
    p_market.add_argument("quantity", type=float)

    # limit
    p_limit = sub.add_parser("limit", help="Place a limit order")
    p_limit.add_argument("symbol")
    p_limit.add_argument("side", choices=["BUY", "SELL"])
    p_limit.add_argument("quantity", type=float)
    p_limit.add_argument("price", type=float)
    p_limit.add_argument("--timeInForce", default="GTC")

    # twap
    p_twap = sub.add_parser("twap", help="Place a TWAP (series of market orders)")
    p_twap.add_argument("symbol")
    p_twap.add_argument("side", choices=["BUY", "SELL"])
    p_twap.add_argument("quantity", type=float)
    p_twap.add_argument("--slices", type=int, default=5)
    p_twap.add_argument("--interval", type=int, default=10, help="seconds between slices")

    # common
    parser.add_argument("--config", default="config.json", help="Path to config file (or set env vars)")

    args = parser.parse_args()
    cfg = load_config(args.config)
    if not cfg.get("API_KEY") or not cfg.get("API_SECRET"):
        logger.error("API key/secret not found. Please fill config.json or set env vars.")
        return

    bot = BasicBot(cfg["API_KEY"], cfg["API_SECRET"], base_url=cfg.get("BASE_URL", "https://testnet.binancefuture.com"), recv_window=cfg.get("RECV_WINDOW", 5000))

    if args.command == "market":
        try:
            res = bot.place_market_order(bot.validate_symbol(args.symbol), bot.validate_side(args.side), args.quantity)
            print("Market order result:", res)
        except Exception as e:
            logger.error("Market order failed: %s", e)

    elif args.command == "limit":
        try:
            res = bot.place_limit_order(bot.validate_symbol(args.symbol), bot.validate_side(args.side), args.quantity, args.price, time_in_force=args.timeInForce)
            print("Limit order result:", res)
        except Exception as e:
            logger.error("Limit order failed: %s", e)

    elif args.command == "twap":
        twap = TWAP(bot, args.symbol, args.side, args.quantity, slices=args.slices, interval_seconds=args.interval)
        results = twap.execute()
        print("TWAP results:")
        for r in results:
            print(r)

if __name__ == "__main__":
    main()
