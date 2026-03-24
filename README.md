# Стандарт РФ — MVP портала нормативных документов

Демонстрационный MVP для ИТ-чемпионата в сфере цифровизации транспорта и ИТС.

## Быстрый старт

```bash
# 1. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить
python run.py
```

Открыть в браузере: **http://localhost:5000**

## Демо-аккаунты

| Роль | Логин | Пароль |
|------|-------|--------|
| Администратор | `admin` | `admin123` |
| Минтранс (Организация) | `mintrans` | `demo123` |
| Росстандарт (Организация) | `rosstandart` | `demo123` |
| Эксперт Смирнов | `smirnov` | `demo123` |
| Эксперт Козлов | `kozlov` | `demo123` |
| Эксперт Соколова | `sokolova` | `demo123` |

> На странице входа можно кликнуть на карточку роли — без ввода пароля.

## Сценарий демонстрации

1. Войти как **Минтранс** → создать новый документ
2. Открыть карточку документа → опубликовать → открыть обсуждение
3. Войти как **Эксперт** → открыть документ → оставить замечание
4. Войти как **Минтранс** → изменить статус замечания (Принято/Отклонено)
5. Войти как **Администратор** → Мониторинг → просмотреть статистику

## Структура проекта

```
standart_rf/
├── app/
│   ├── __init__.py          # Flask app factory + context processor
│   ├── models.py            # SQLAlchemy модели
│   ├── seed.py              # Демо-данные
│   ├── utils.py             # Декораторы login_required, role_required
│   ├── routes/
│   │   ├── auth.py          # Авторизация + demo-login
│   │   ├── main.py          # Dashboard (роль-зависимый)
│   │   ├── documents.py     # CRUD документов + комментарии
│   │   ├── admin.py         # Управление пользователями, рубриками, мониторинг
│   │   ├── rubrics.py       # Рубрикатор
│   │   ├── notifications.py # Уведомления
│   │   └── messages.py      # Внутренние сообщения
│   ├── templates/
│   │   ├── base.html        # Базовый layout (sidebar + topbar)
│   │   ├── auth/            # Страница входа
│   │   ├── dashboard/       # Дашборды admin / org / expert
│   │   ├── documents/       # Список, карточка, форма добавления
│   │   ├── admin/           # Пользователи, рубрики, мониторинг
│   │   ├── rubrics/         # Рубрикатор
│   │   ├── notifications/   # Уведомления
│   │   └── messages/        # Сообщения
│   └── static/
│       ├── css/main.css     # Кастомные стили
│       └── js/main.js       # JS-утилиты
├── config.py
├── run.py
└── requirements.txt
```

## Стек

- **Backend:** Python 3.10+ / Flask 3.0
- **ORM:** SQLAlchemy / SQLite
- **Frontend:** Jinja2 + Bootstrap 5.3 + Bootstrap Icons + Chart.js
- **Auth:** Session-based (demo)
