import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Type, List, Tuple
from tqdm import tqdm


class Move(StrEnum):
    ROCK = "ROCK"
    PAPER = "PAPER"
    SCISSOR = "SCISSOR"


@dataclass
class HistoryEntry:
    self: Move
    other: Move


History = Tuple[HistoryEntry, ...]


class Strategy(ABC):
    @abstractmethod
    def begin(self) -> Move:
        """ """
        ...

    @abstractmethod
    def turn(self, history: History) -> Move:
        """ """
        ...


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
    ROUNDS: Final[int] = 10_000
    TIMEOUT_SECONDS: Final[int] = 60

    def __init__(self, strategy_cls: Type[Strategy]) -> None:
        self.wins: int = 0
        self.losses: int = 0
        self.draws: int = 0
        self.strategy_cls = strategy_cls

    def run(self) -> None:
        try:
            strategy = self.strategy_cls()
        except Exception as e:
            raise AssertionError(f"Strategy failed to initialize: {e}")

        opponent = RandomStrategy()

        history_self: List[HistoryEntry] = []
        history_opp: List[HistoryEntry] = []

        print("Testing against RandomStrategy")

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

        for _ in tqdm(range(self.ROUNDS - 1), desc="Running rounds"):
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

            if (
                move_self == Move.ROCK
                and move_opp == Move.SCISSOR
                or move_self == Move.PAPER
                and move_opp == Move.ROCK
                or move_self == Move.SCISSOR
                and move_opp == Move.ROCK
            ):
                self.wins += 1
            elif move_self != move_opp:
                self.losses += 1
            else:
                self.draws += 1

        total_time = time.time() - start_time
        print(f"✅ PASS: {StrategyTester.ROUNDS} rounds in {total_time:.2f} seconds")
        print(f"{self.wins} Wins, {self.losses} Losses, {self.draws} Draws")


__all__ = ["History", "HistoryEntry", "Move", "Strategy", "StrategyTester"]
