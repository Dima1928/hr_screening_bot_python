from app.models.message import ConversationMessage, MessageRole
from app.repositories.history import InMemoryHistoryRepository


def test_history_add_and_list_messages() -> None:
    repo = InMemoryHistoryRepository()

    repo.add("cand-1", ConversationMessage(role=MessageRole.CANDIDATE, text="Привет"))
    repo.add("cand-1", ConversationMessage(role=MessageRole.BOT, text="Расскажите про опыт?"))

    history = repo.list("cand-1")

    assert len(history) == 2
    assert history[0].text == "Привет"
    assert history[1].role == MessageRole.BOT
