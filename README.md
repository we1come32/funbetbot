# Бот для ставок на спорт

*является фан-проектом*

Плюсы:
- Реальные деньги не имеют значения
- Отсутствие вывода игровой валюты
- Коэффициенты от реальных букмекеров
- Никаких сайтов - всё реализовано в виде взаимодействия с <a href="https://t.me/virtualbetbot">ботом Telegram</a>

Минусы:
- Отсутствие интеграции с другими социальными сетями

---

# Установка и запуск

Устанавливать бота для его использования нет необходимости: достаточно <a href="https://t.me/virtualbetbot">существующего 
бота Telegram</a>

1) Установить Python 3.10+
2) Установить pip - менеджер пакетов Python
3) Создать виртуальное окружение: `python3 -m venv myvenv .` (для Windows `python -m venv myvenv .`) (точка обязательна)
4) Активировать виртуальное окружение `source ./myvenv/bin/Activate` (для Windows `./myvenv/Scripts/activate.bat`)
5) Скачать репозиторий `git clone git+/github.com/we1come32/funbetbot`
6) Установить зависимости `pip install -r requirements.txt`
7) Создать своего бота у <a href="https://t.me/botfather">@BotFather</a>, получить ключ доступа бота
8) Вставить ключ доступа в `config.py` в переменную `ACCESS_TOKEN`
9) Сделать миграции с базой данных: `python manage.py migrate`
10) Для запуска бота: `python main.py`
11) Для запуска мониторинга событий: `python background_tasks.py`

---

# Ссылки проекта в Telegram:

- <a href="https://t.me/virtualbetbot">Бот - Ставки на спорт</a> - ссылка на бота
- <a href="https://t.me/virtualbetchannel">Бот - Ставки на спорт [СОБЫТИЯ]</a> - ссылка на канал с новыми поддерживаемыми 
ботом событиями
- <a href="https://t.me/virtualbetchannel_dev">Бот - ставки на спорт [DEV]</a> - сылка на канал разработчиков бота с обновлениями, 
инсайдами будущих обновлений, опросами
