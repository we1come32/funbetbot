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

1) Установить Python 3.8+
2) Установить pip - менеджер пакетов Python
3) Скачать репозиторий `git clone git+/github.com/we1come32/funbetbot`
4) Установить зависимости `pip3 install -r requirements.txt` 
(для Windows `pip install -r requirements.txt`)
5) Создать своего бота у <a href="https://t.me/botfather">@BotFather</a>, получить ключ доступа бота
6) Вставить ключ доступа в `config.py` в переменную `ACCESS_TOKEN`
7) `python3 main.py` (для Windows `python main.py`)

---
