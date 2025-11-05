This package contains simple driver code + testing functionality for @ping/game-theory-25

# Types


## `Move` (Enum)
```python
class Move(StrEnum):
    ROCK = "ROCK"
    PAPER = "PAPER"
    SCISSOR = "SCISSOR"
```
Represents a single move in the game.


## `HistoryEntry` (Dataclass)
```py
@dataclass
class HistoryEntry:
    self: Move
    other: Move
```
Represents the result of one round of play between two strategies.

| Field   | Type   | Meaning                            |
| ------- | ------ | ---------------------------------- |
| `self`  | `Move` | The move played by *this* strategy |
| `other` | `Move` | The move played by the opponent    |


## `History` (Type Alias)
```py
History = Tuple[HistoryEntry, ...]
```
A read-only sequence of all previous rounds. Each element is a `HistoryEntry`. The most recent round is at the **end** of the tuple.


## `Strategy` (Abstract Base Class)
```py
class Strategy(ABC):
    @abstractmethod
    def begin(self) -> Move:
        ...

    @abstractmethod
    def turn(self, history: History) -> Move:
        ...
```
Base class for all strategies (bots).
Every strategy must implement two methods:
| Method          | Called When                 | Purpose                                         |
| --------------- | --------------------------- | ----------------------------------------------- |
| `begin()`       | Before the first round      | Returns the first move                          |
| `turn(history)` | Every round after the first | Returns the next move based on previous history |

Any class that does **not** implement both methods cannot be instantiated.


# Example Strategy
```py
class ILoveRocks(Strategy):
    def __init__(self) -> None:
        self.author_netid = "lm742"
        self.strategy_name = "ILoveRocks"
        self.strategy_desc = "I really love rocks"

    def begin(self) -> Move:
        return Move.ROCK

    def turn(self, history: History) -> Move:
        return Move.ROCK
```

# Strategy Tester
To ensure every strategy follows the required interface and runs efficiently, the project includes a built-in tester: `StrategyTester`

The tester automatically checks:
| Check              | What it verifies                                         |
| ------------------ | -------------------------------------------------------- |
| **Initialization** | Your strategy's `__init__` runs without errors           |
| **Return types**   | `begin()` and `turn()` must always return a valid `Move` |
| **No exceptions**  | Your strategy must never crash during play               |
| **Performance**    | Must complete `10,000` rounds within `60 seconds`        |

If your strategy passess all checks, you will see:
```py
✅ PASS: 10000 rounds in X.XX seconds
```

## How to Test your Strategy
You must pass in your strategy class **without** instantiating it
```py
if __name__ == "__main__":
    tester = StrategyTester(ILoveRocks)
    tester.run()
```