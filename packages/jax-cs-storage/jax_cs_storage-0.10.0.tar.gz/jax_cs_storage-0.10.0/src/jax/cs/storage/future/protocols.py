from typing import TypeVar, Protocol

T = TypeVar('T')

class Downloadable(Protocol):

    def download(self) -> T:
        ...