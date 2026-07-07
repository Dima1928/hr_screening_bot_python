from datetime import datetime, timedelta, timezone
from threading import RLock

from app.models.screening import InterviewSlot
from app.models.vacancy import Vacancy


class CalendarSimulator:
    """Имитация интеграции с календарем рекрутера.

    В реальном проекте здесь была бы интеграция с Google Calendar, Outlook или HRM.
    По заданию планирование можно симулировать.
    """

    def __init__(self) -> None:
        self._booked: dict[str, InterviewSlot] = {}
        self._lock = RLock()

    def get_free_slots(self, vacancy: Vacancy, count: int = 3) -> list[InterviewSlot]:
        recruiter = vacancy.recruiter_email or "recruiter@example.com"
        start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        slots: list[InterviewSlot] = []

        # Несколько ближайших рабочих слотов, достаточно для демонстрации.
        offset_hours = 24
        while len(slots) < count:
            candidate_start = start + timedelta(hours=offset_hours)
            if candidate_start.hour < 9:
                candidate_start = candidate_start.replace(hour=10)
            if candidate_start.hour > 17:
                candidate_start = (candidate_start + timedelta(days=1)).replace(hour=10)
            if candidate_start.weekday() < 5:
                candidate_end = candidate_start + timedelta(minutes=45)
                slot_id = f"slot-{candidate_start.strftime('%Y%m%d%H%M')}"
                if slot_id not in self._booked:
                    slots.append(
                        InterviewSlot(
                            slot_id=slot_id,
                            starts_at=candidate_start.isoformat(),
                            ends_at=candidate_end.isoformat(),
                            recruiter=recruiter,
                        )
                    )
            offset_hours += 3
        return slots

    def book(self, slot: InterviewSlot) -> InterviewSlot:
        with self._lock:
            self._booked[slot.slot_id] = slot
        return slot
