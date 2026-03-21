# Тесты Discord Clone

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ -v --cov=app --cov-report=html

# Конкретный модуль
pytest tests/test_auth.py -v

# С логированием
pytest tests/ -v -s