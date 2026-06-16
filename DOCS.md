# Документация проекта: VTubers Online Over Time

Этот документ содержит техническое описание проекта, механизмы обхода ограничений TwitchTracker и руководство по использованию скриптов.

---

## 🔒 Механизм деобфускации TwitchTracker

TwitchTracker не отдаёт статистику в открытом HTML-коде и защищает её от прямого парсинга с помощью скрытых метатегов `<meta id="ecs">` с зашифрованным содержимым.

### Схема работы обфускации:
1. **Основной HTML:**
   При открытии `https://twitchtracker.com/{streamer}` отдаётся базовая разметка. В ней находится тег `<meta id="ecs" content="...">`.
2. **Формат строки шифрования:**
   Значение атрибута `content` состоит из 3 частей, разделённых знаком восклицания `!`.
   Символы `#` в этих строках заменяют букву `W`.
3. **Процесс декодирования:**
   * Строка разбивается по `!`.
   * В каждой части символ `#` заменяется на `W`.
   * Каждая часть декодируется из Base64.
   * Последняя часть — это массив ключей (например, `["related", "fragments"]`).
   * Первая часть содержит список похожих стримеров, а вторая — одноразовый подписанный URL-адрес для загрузки фрагментов страницы:
     `https://twitchtracker.com/{streamer}/fragments?expires=TIMESTAMP&signature=SIGNATURE`
4. **Запрос фрагментов:**
   Клиент отправляет POST-запрос на этот URL с заголовком `X-Requested-With: XMLHttpRequest` и телом `{'id': channel_id}` (ID канала Twitch).
5. **Второй уровень шифрования:**
   В ответе на этот POST-запрос приходит HTML-код фрагментов, содержащий **ещё один** тег `<meta id="ecs" content="...">`.
   Его декодирование по той же схеме даёт ключи `["performance", "charts"]`.
   * В секции `charts` -> `statistics` лежит искомый массив ежемесячной статистики:
     `[Дата, Avg Viewers, Peak Viewers, Minutes Streamed, Followers Gain, Game Weights]`

---

## 📂 Описание скриптов проекта

В корне проекта расположены основные рабочие скрипты:

### Основные скрипты сбора и обработки

* **`scrape_all_vtubers.py`**
  Основной скрипт пакетного сбора данных.
  * Читает никнеймы из [data/vtubers.txt](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers.txt).
  * Делает запросы к TwitchTracker с вежливой случайной задержкой от 1 до 3 секунд между стримерами для предотвращения блокировок IP.
  * Работает в режиме **дозаписи** — если скрипт прервать, при следующем запуске он прочтет уже обработанные каналы из выходного CSV и пропустит их.
  * Сохраняет статистику по месяцам в файл [data/vtubers_avg_online.csv](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers_avg_online.csv) в длинном формате (`month,vtuber,avg_viewers`).

* **`create_wide_dataset.py`**
  Скрипт трансформации данных в широкий формат для визуализации.
  * Читает [data/vtubers_avg_online.csv](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers_avg_online.csv).
  * Формирует единый упорядоченный список месяцев (столбцов).
  * Делает запросы к публичному API `https://api.ivr.fi/v2/twitch/user?login={username}` с задержкой 0.5 секунд, чтобы получить ссылки на аватарки стримеров.
  * Использует кэш [data/vtuber_images_cache.json](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtuber_images_cache.json) для аватарок, чтобы не нагружать API повторно.
  * При возникновении ошибок или 404 (удаленные каналы) проставляет дефолтный аватар.
  * Заполняет недостающие месяцы нулями (`0`).
  * Сохраняет результат в [data/vtubers_wide_stats.csv](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers_wide_stats.csv).

---

### 📁 Папка [drafts/](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts) (Устаревшие скрипты и черновики)

Для поддержания чистоты корня проекта все тестовые утилиты и прототипы перенесены в отдельную директорию:

* **[drafts/demonstrate_extraction.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/demonstrate_extraction.py)** — демонстрационный скрипт, содержащий чистую реализацию обхода шифрования и парсинга для одного стримера без внешних зависимостей.
* **[drafts/fetch_streamer_data.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/fetch_streamer_data.py)** — утилита для быстрого получения данных об одном стримере в JSON-формат.
* **[drafts/decode.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/decode.py)** — первый драфт дешифратора метаданных с TwitchTracker.
* **[drafts/fetch_fragments.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/fetch_fragments.py)** — утилита для тестирования POST-запросов фрагментов.
* **[drafts/parse_rows.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/parse_rows.py)** — парсинг списка трансляций из сохраненного фрагмента.
* **[drafts/parse_streams.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/parse_streams.py)** — извлечение чисел и блоков из фрагментов.
* **[drafts/search_html.py](file:///C:/FRA3A/projects/vtubers-online-over-time/drafts/search_html.py)** — вспомогательный поиск по скачанным HTML-файлам.

---

## 📊 Структуры файлов данных

### Входные данные:
* **[data/vtubers.txt](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers.txt)** — текстовый файл с никнеймами стримеров (один в строке).

### Выходные данные:
* **[data/vtubers_avg_online.csv](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers_avg_online.csv)** — длинный формат:
  ```csv
  month,vtuber,avg_viewers
  2026-01-01,megubite,83
  2026-02-01,megubite,74
  ```
* **[data/vtubers_wide_stats.csv](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtubers_wide_stats.csv)** — широкий формат с выровненными датами и аватарками:
  ```csv
  Label,Image URL,2016-11-01,2016-12-01,...,2026-06-01
  megubite,https://static-cdn.jtvnw.net/...,0,0,...,51
  hatome,https://static-cdn.jtvnw.net/...,0,0,...,27
  ```
* **[data/vtuber_images_cache.json](file:///C:/FRA3A/projects/vtubers-online-over-time/data/vtuber_images_cache.json)** — кэш аватарок Twitch.

