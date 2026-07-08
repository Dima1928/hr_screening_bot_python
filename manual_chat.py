import json
import urllib.request


URL = "http://127.0.0.1:8090/webhook"


def send_message(candidate_id: str, candidate_name: str, vacancy_id: str, text: str) -> dict:
    payload = {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "vacancy_id": vacancy_id,
        "text": text,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    candidate_id = input("ID кандидата, например test-1: ").strip() or "test-1"
    candidate_name = input("Имя кандидата: ").strip() or "Иван"
    vacancy_id = input("ID вакансии, например python_backend: ").strip() or "python_backend"

    print("\nПиши сообщения кандидата. Для выхода напиши exit.\n")

    while True:
        text = input("Кандидат: ").strip()
        if text.lower() in {"exit", "quit", "выход"}:
            break

        try:
            result = send_message(candidate_id, candidate_name, vacancy_id, text)
        except Exception as error:
            print(f"\nОшибка запроса: {error}\n")
            continue

        print("\nБот:")
        print(result.get("reply"))
        print("\nТекущий этап:")
        print(result.get("stage"))

        recommendation = result.get("recommendation")
        if recommendation:
            print("\nРекомендация:")
            print(json.dumps(recommendation, ensure_ascii=False, indent=2))

        slots = result.get("interview_slots", [])
        if slots:
            print("\nДоступные слоты:")
            for slot in slots:
                print(f"- {slot['slot_id']}: {slot['starts_at']} — {slot['ends_at']}")
        print()


if __name__ == "__main__":
    main()
