from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Tuple


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
