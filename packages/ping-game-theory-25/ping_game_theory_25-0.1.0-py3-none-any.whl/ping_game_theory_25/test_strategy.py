import random
import time
from typing import Final, List, Type

from utils import Move, Strategy, History, HistoryEntry


class RandomStrategy(Strategy):
    def __init__(self) -> None:
        self.author_netid = "ab123"
        self.strategy_name = "random"
        self.strategy_description = "random"

    def begin(self) -> Move:
        return random.choice(list(Move))

    def turn(self, history: History) -> Move:
        return self.begin()


class StrategyTester:
    ROUNDS: Final[int] = 1_000_000
    TIMEOUT_SECONDS: Final[int] = 60

    def __init__(self, strategy_cls: Type[Strategy]) -> None:
        self.strategy_cls = strategy_cls

    def run(self) -> None:
        try:
            strategy = self.strategy_cls()
        except Exception as e:
            raise AssertionError(f"Strategy failed to initialize: {e}")

        opponent = RandomStrategy()

        history_self: List[HistoryEntry] = []
        history_opp: List[HistoryEntry] = []

        start_time = time.time()
        try:
            move_self = strategy.begin()
            move_opp = opponent.begin()
        except Exception as e:
            raise AssertionError(f"begin() raised an exception: {e}")

        if not isinstance(move_self, Move):
            raise AssertionError(f"begin() returned invalid type: {type(move_self)}")

        history_self.append(HistoryEntry(self=move_self, other=move_opp))
        history_opp.append(HistoryEntry(self=move_opp, other=move_self))

        for _ in range(self.ROUNDS - 1):
            if time.time() - start_time > StrategyTester.TIMEOUT_SECONDS:
                raise TimeoutError(
                    f"Execution exceeded timeout of {StrategyTester.TIMEOUT_SECONDS} seconds"
                )

            try:
                move_self = strategy.turn(tuple(history_self))
            except Exception as exc:
                raise AssertionError(f"turn() raised an exception: {exc}")

            move_opp = opponent.turn(tuple(history_opp))

            if not isinstance(move_self, Move):
                raise AssertionError(f"turn() returned invalid type: {type(move_self)}")

            history_self.append(HistoryEntry(self=move_self, other=move_opp))
            history_opp.append(HistoryEntry(self=move_opp, other=move_self))

        total_time = time.time() - start_time
        print(f"✅ PASS: {StrategyTester.ROUNDS} rounds in {total_time:.2f} seconds")
