# HR Screening Bot на Python

Учебный микросервис для задания **«Бот для HR с автоматизацией первичного скрининга кандидатов»**.

Сервис принимает входящие сообщения кандидата через webhook, задает предквалификационные вопросы, анализирует ответы по требованиям вакансии, формирует рекомендацию и либо предлагает слоты интервью, либо отправляет вежливый отказ с обратной связью.

## Почему сделано так

По общим требованиям бот должен подключаться к СпросиИИ через webhooks. В условиях задания доступа к СпросиИИ нет, поэтому реализован совместимый входной endpoint:

```text
POST /webhook
```

Его можно дергать любым внешним сервисом, Postman, curl или контейнером-симулятором в `docker-compose.yml`.

Вместо внутренней языковой модели СпросиИИ используется DeepSeek через обычный POST-запрос:

```text
POST {LLM_API_BASE_URL}/chat/completions
Authorization: Bearer {LLM_API_KEY}
```

Для локальной проверки без API-ключа есть режим `LLM_MODE=stub`. В нем бот работает детерминированно, тесты проходят без интернета и без реального DeepSeek.

## Реализованная функциональность

- прием сообщений кандидата через webhook;
- выбор вакансии по `vacancy_id`;
- хранение истории диалога кандидата;
- адаптивные предквалификационные вопросы;
- оценка опыта, навыков и зарплатных ожиданий;
- проверка соответствия базовым требованиям вакансии;
- рекомендация: `подходит`, `не подходит`, `требуется уточнение`;
- формирование резюме беседы для рекрутера;
- симуляция календаря и выдача доступных слотов интервью;
- вежливый отказ с обратной связью для неподходящих кандидатов;
- Docker-контейнеризация;
- тесты в стиле TDD через `pytest`;
- описание Git Flow.

## Стек

- Python 3.12;
- FastAPI;
- Pydantic;
- httpx;
- pytest;
- Docker / Docker Compose.

## Структура проекта

```text
hr_screening_bot_python/
├── app/
│   ├── api/
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── data/
│   │   └── vacancies.json
│   ├── llm/
│   │   ├── base.py
│   │   ├── deepseek.py
│   │   └── stub.py
│   ├── models/
│   │   ├── message.py
│   │   ├── screening.py
│   │   └── vacancy.py
│   ├── repositories/
│   │   ├── history.py
│   │   └── vacancy.py
│   ├── scheduler/
│   │   └── calendar.py
│   ├── services/
│   │   └── processor.py
│   └── main.py
├── tests/
├── docs/
│   └── openapi.yaml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Быстрый запуск локально

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r requirements-dev.txt
```

Создание `.env`:

```bash
cp .env.example .env
```

Запуск:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

Проверка:

```bash
curl http://localhost:8090/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Запуск через Docker

```bash
cp .env.example .env
```

```bash
docker compose up --build
```

Сервис будет доступен на:

```text
http://localhost:8090
```

Документация FastAPI:

```text
http://localhost:8090/docs
```

## Режимы работы LLM

### 1. Локальный режим без API-ключа

В `.env`:

```env
LLM_MODE=stub
```

Так проект можно показать преподавателю и прогнать тесты без внешних сервисов.

### 2. Реальный DeepSeek через POST

В `.env`:

```env
LLM_MODE=deepseek
LLM_API_BASE_URL=https://api.deepseek.com
LLM_API_KEY=ваш_api_ключ
LLM_MODEL=deepseek-chat
```

Клиент находится в файле:

```text
app/llm/deepseek.py
```

Он отправляет POST-запрос на `/chat/completions` и просит модель возвращать строгий JSON, чтобы сервис мог надежно обработать результат.

## Пример запроса в webhook

```bash
curl -X POST http://localhost:8090/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "cand-1",
    "candidate_name": "Иван Петров",
    "vacancy_id": "python_backend",
    "text": "Здравствуйте, хочу откликнуться на вакансию Python backend разработчика"
  }'
```

Пример ответа:

```json
{
  "candidate_id": "cand-1",
  "vacancy_id": "python_backend",
  "stage": "in_progress",
  "reply": "Иван, расскажите, пожалуйста, о последнем релевантном опыте для вакансии «Python Backend Developer»: сколько лет опыта и какие задачи выполняли?",
  "recommendation": null,
  "interview_slots": []
}
```

После нескольких ответов кандидата бот выдаст рекомендацию. Для подходящего кандидата пример этапа:

```json
{
  "stage": "qualified",
  "recommendation": {
    "status": "подходит",
    "score": 95,
    "summary": "Кандидат в целом соответствует базовым требованиям вакансии."
  },
  "interview_slots": [
    {
      "slot_id": "slot-202607081000",
      "starts_at": "2026-07-08T10:00:00+00:00",
      "ends_at": "2026-07-08T10:45:00+00:00",
      "recruiter": "hr-python@example.com"
    }
  ]
}
```

## Вакансии

Вакансии лежат в файле:

```text
app/data/vacancies.json
```

Сейчас добавлены примеры:

- `python_backend`;
- `hr_generalist`.

Можно добавить свои вакансии, не меняя код.

## Тесты

Запуск:

```bash
pytest -q
```

Или через Makefile:

```bash
make test
```

Что проверяется:

- загрузка вакансий;
- хранение истории диалога;
- webhook endpoint;
- бизнес-логика скрининга;
- выдача слотов интервью;
- отказ неподходящему кандидату;
- реальный формат POST-запроса DeepSeek `/chat/completions` через mock HTTP transport.

## Git Flow

Проект предполагает версионирование через Git Flow:

```text
main      — стабильная версия, которую можно сдавать / деплоить
release   — подготовка релиза, финальная проверка перед main
develop   — основная ветка разработки
feature/* — отдельные задачи и фичи
```

Пример:

```bash
git checkout -b develop
```

```bash
git checkout -b feature/webhook-handler
```

После разработки:

```bash
git checkout develop
git merge feature/webhook-handler
```

Перед сдачей:

```bash
git checkout -b release/1.0.0
pytest -q
git checkout main
git merge release/1.0.0
git tag v1.0.0
```

## Как это закрывает требования задания

| Требование | Реализация |
|---|---|
| Отдельный микросервис | FastAPI-приложение в `app/main.py` |
| Webhooks | `POST /webhook` |
| Нет доступа к СпросиИИ | Endpoint совместим с внешним webhook-источником, можно подключить позже |
| Обращение к LLM | DeepSeek через POST `/chat/completions` |
| Внутренняя сеть Docker / порты | `docker-compose.yml`, порт `8090`, обращение по имени сервиса внутри сети |
| TDD | тесты в папке `tests/`, запуск `pytest -q` |
| Docker | `Dockerfile` и `docker-compose.yml` |
| Git Flow | описан в README |
| Предквалификационные вопросы | `LLMClient.next_question()` |
| Оценка опыта, навыков, ожиданий | `LLMClient.analyze_candidate()` |
| Проверка требований | требования вакансии в `vacancies.json` |
| Резюме беседы и рекомендация | модель `ScreeningAnalysis` |
| Планирование интервью | `CalendarSimulator` |
| Вежливый отказ | формируется при статусе `не подходит` |

## Команды для демонстрации преподавателю

```bash
cp .env.example .env
```

```bash
docker compose up --build
```

В другом терминале:

```bash
curl -X POST http://localhost:8090/webhook \
  -H "Content-Type: application/json" \
  -d '{"candidate_id":"demo-1","candidate_name":"Иван","vacancy_id":"python_backend","text":"Здравствуйте, хочу откликнуться"}'
```

Проверка тестов:

```bash
pytest -q
```
