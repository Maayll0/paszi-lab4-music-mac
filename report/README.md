# Материалы для отчёта

Порядок показа преподавателю и ожидаемые результаты: [сценарий защиты](defense-scenario.md).

Локальные кадры в `screenshots/` создаются браузерными тестами с `CAPTURE_REPORT=1`:

1. `01-weak-password.png` — отказ слабому паролю.
2. `02-registration.png` — форма, email и чекбокс.
3. `03-registration-success.png` — успешная регистрация.
4. `04-duplicate-login.png` — занятый логин.
5. `05-authenticated-catalogue.png` — вход, логин и Public в шапке.
6. `06-search-suggestions.png` — раскрытые подсказки.
7. `07-url-filters.png` — результат title + artist.
8. `08-public-player.png` — воспроизведение Public → Public, время и прогресс.
9. `09-access-denied.png` — реальный отказ Public → Confidential, страница 403.

Дополнительно снимите для методички:

- Страницу `/login` и успешный вход.
- Адресную строку `/music?title=Night&artist=Electronic`, переходы «Назад»/«Вперёд».
- Network в DevTools: `/stream` со статусами 206 и 403.
- Входы demo_confidential и demo_secret с соответствующими разрешениями.
- Таблицы PostgreSQL: SELECT из README показывает только префикс хэша, без секретов.
- Итог `pytest`, успешные проверки GitHub Actions и `docker compose ps`.
- GitHub PR и историю коммитов с автором и соавтором.
- Форму удаления аккаунта и переход ко входу после удаления.
