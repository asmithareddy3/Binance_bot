# src/twap.py
import time
import math
from basic_bot import BasicBot
from logger_setup import setup_logger

logger = setup_logger("twap_bot", log_file="twap.log")

class TWAP:
    def __init__(self, bot: BasicBot, symbol: str, side: str, total_qty: float, slices: int = 5, interval_seconds: int = 10):
        self.bot = bot
        self.symbol = bot.validate_symbol(symbol)
        self.side = bot.validate_side(side)
        self.total_qty = float(total_qty)
        self.slices = max(1, int(slices))
        self.interval_seconds = max(1, int(interval_seconds))
        logger.info("TWAP init %s %s total=%s slices=%s interval=%ss", self.symbol, self.side, self.total_qty, self.slices, self.interval_seconds)

    def execute(self):
        slice_qty = self.total_qty / self.slices
        results = []
        for i in range(self.slices):
            logger.info("TWAP slice %d/%d placing market order qty=%s", i+1, self.slices, slice_qty)
            try:
                res = self.bot.place_market_order(self.symbol, self.side, quantity=slice_qty)
                logger.info("TWAP slice %d result: %s", i+1, res)
                results.append(res)
            except Exception as e:
                logger.exception("TWAP slice %d failed: %s", i+1, e)
                results.append({"error": str(e)})
            if i != self.slices - 1:
                time.sleep(self.interval_seconds)
        return results
