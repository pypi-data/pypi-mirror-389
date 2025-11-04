# tgmrkt-api - Wrapper для TG MRKT API

Простой синхронный Python wrapper для [Telegram MRKT API](https://tgmrkt.io) - NFT маркетплейса для торговли подарками и стикерами в Telegram.

## Возможности

✅ Поиск и фильтрация подарков  
✅ Парсинг полных коллекций  
✅ Получение статистики коллекций (минимальная, максимальная, средняя, медианная цена)  
✅ Экспорт данных в CSV  
✅ Мониторинг флор с логированием  
✅ Получение соревнований/событий  
✅ Автоматическая обработка пагинации  

## Установка

```bash
pip install tgmrkt-api
```

## Быстрый старт

```python
from mrkt_api import parse_collection_full, get_collection_stats, export_to_csv

# Твой токен аутентификации из DevTools Network tab
auth = "your-token-here"

# Парсим коллекцию
gifts = parse_collection_full(auth, "Ice Cream", max_pages=5)

# Получаем статистику
stats = get_collection_stats(auth, "Ice Cream")
print(f"Floor: {stats['floor_ton']:.9f} TON")

# Экспортируем в CSV
export_to_csv(auth, "gifts.csv", collection="Ice Cream", max_items=100)
```

## Как получить токен аутентификации

1. Открой [tgmrkt.io](https://tgmrkt.io) в браузере
2. Открой DevTools (F12)
3. Перейди на вкладку Network
4. Сделай любой запрос (поиск, загрузка страницы и т.д.)
5. Найди запрос к `api.tgmrkt.io`
6. В заголовках запроса найди: `Authorization: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
7. Скопируй этот токен

## Справочник API

### Поиск и просмотр

```python
# Поиск подарков с фильтрами
search_gifts(auth, model_names=["Albino"], count=20)

# Получить мои/видимые подарки
my_gifts(auth, count=20)

# Получить все названия подарков
get_all_gift_names(auth, max_count=1000)

# Парсить полную коллекцию (все товары на продажу)
parse_collection_full(auth, "Ice Cream", max_pages=100)
```

### Статистика и цены

```python
# Получить статистику коллекции
get_collection_stats(auth, "Ice Cream", max_pages=10)
# Возвращает: floor, ceil, avg, median цены, количество на продажу

# Получить топ-N коллекций по цене floor
get_top_floors(auth, n=5)

# Получить цену floor для конкретной коллекции
get_collection_floor(auth, "Ice Cream")

# Получить floors для всех коллекций (из листингов на продажу)
get_collection_floors_from_saling(auth, max_pages=10)
```

### Мониторинг и логирование

```python
# Мониторить floors с периодическими проверками
monitor_floors(
    auth,
    collections=["Ice Cream", "Desk Calendar"],
    interval_sec=300,           # Проверять каждые 5 минут
    duration_sec=3600,          # В течение 1 часа
    log_file="monitor.json"     # Сохранять логи
)

# Для бесконечного мониторинга используй duration_sec=-1
```

### Экспорт

```python
# Экспортировать подарки в CSV
export_to_csv(auth, "gifts.csv", collection="Ice Cream", max_items=500)

# Экспортировать floors всех коллекций в CSV
export_collection_floors(auth, "floors.csv", max_pages=10)
```

### Другое

```python
# Получить соревнования/события
get_competitions(auth)

# Получить Telegram Stars подарки
get_stars_gifts(auth)

# Получить коллекции стикеров
get_sticker_collections(auth)

# Конвертировать nanoTON в TON
nano_to_ton(1_000_000_000)  # Возвращает 1.0
```

## Примеры

Смотри `examples.py` для детальных примеров использования:

- Парсинг полной коллекции
- Получение статистики коллекции
- Экспорт данных
- Мониторинг флор
- Поиск с фильтрами
- Поиск выгодных предложений

```bash
python examples.py
```

## Обработка ошибок

```python
from mrkt_api import parse_collection_full

try:
    gifts = parse_collection_full(auth, "Collection", max_pages=5)
except ValueError as e:
    print(f"Ошибка API: {e}")
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
```

Частые ошибки:
- `Auth expired` - Токен истёк, получи новый из DevTools
- `Endpoint not found` - Неправильный endpoint
- `Request timeout` - API медленное, попробуй позже

## Формат данных

### Объект Gift

```python
{
    'name': 'IceCream-12345',           # ID подарка
    'number': 12345,                    # Номер подарка
    'title': 'Sweet Drip',              # Название подарка
    'model': 'Shiny Silk',              # Тип модели
    'backdrop': 'Minty',                # Фон/тема
    'symbol': 'Cherry',                 # Тип символа
    'price_ton': 1.254,                 # Цена в TON
    'price_nano': 1254000000,           # Цена в nanoTON
    'model_rarity': 25,                 # Редкость модели (per mille)
    'backdrop_rarity': 15,              # Редкость фона
    'symbol_rarity': 6,                 # Редкость символа
    'total_rarity': 46,                 # Сумма редкостей
    'gift_type': 'Upgraded',            # Тип подарка
    'id': 'uuid'                        # Уникальный ID
}
```

### Статистика коллекции

```python
{
    'collection': 'Ice Cream',
    'count_on_sale': 50,
    'floor_ton': 1.254,
    'ceil_ton': 2.5,
    'avg_ton': 1.35,
    'median_ton': 1.32,
    'total_items_scanned': 50
}
```

## Ограничения по скорости

API не имеет задокументированных лимитов, но будь вежлив:
- Не спамь запросы в циклах
- Используй разумные интервалы для мониторинга (300+ секунд)
- По возможности группируй запросы

## Ограничения

- Поддерживает только поиск/просмотр подарков (покупка/продажа еще нет)
- Только синхронный код (async поддержка планируется)
- Требует валидный токен аутентификации

## Помощь в разработке

Issues и Pull Requests приветствуются! Пожалуйста, сообщай:
- Ошибки API с текстом ошибки
- Неожиданные форматы данных
- Запросы новых возможностей

## Лицензия

MIT License - Смотри файл LICENSE

## Отказ от ответственности

Это неофициальный wrapper. Используй на свой риск. Не аффилирован с Telegram или MRKT.

## Ссылки

- [MRKT Официальный сайт](https://tgmrkt.io)
- [PyPI](https://pypi.org/project/mrkt-api)