import typing as t
from dataclasses import dataclass

T = t.TypeVar("T")


@dataclass
class PaginatorPage(t.Generic[T]):
    index: int
    pages_count: int
    items: tuple[T, ...]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    def __bool__(self) -> bool:
        return bool(self.items)
