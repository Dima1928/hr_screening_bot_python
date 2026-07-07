from collections import defaultdict
from copy import deepcopy
from threading import RLock

from app.models.message import ConversationMessage


class InMemoryHistoryRepository:
    """Простое хранилище истории диалога.

    Для учебного микросервиса этого достаточно. При необходимости класс легко
    заменить Redis-репозиторием без изменения бизнес-логики.
    """

    def __init__(self) -> None:
        self._data: dict[str, list[ConversationMessage]] = defaultdict(list)
        self._lock = RLock()

    def add(self, candidate_id: str, message: ConversationMessage) -> None:
        with self._lock:
            self._data[candidate_id].append(message)

    def list(self, candidate_id: str) -> list[ConversationMessage]:
        with self._lock:
            return deepcopy(self._data.get(candidate_id, []))

    def clear(self, candidate_id: str) -> None:
        with self._lock:
            self._data.pop(candidate_id, None)
