# SyncManager

Ranobe Manager — это приложение для управления библиотекой ранобэ. Оно позволяет работать с несколькими источниками, управлять аккаунтами, кешировать изображения и предоставлять удобный интерфейс для чтения и навигации.

## Особенности

- Поддержка популярных платформ: [`Rulate`](https://tl.rulate.ru), [`RanobeRF`](https://xn--80ac9aeh6f.xn--p1ai/), [`RanobeHub`](https://ranobehub.org/), [`RanobeLib`](https://ranobelib.me/).
- Загрузка и управление данными о книгах (названия, описания, ссылки, главы и т. д.).
- Автоматическое кеширование изображений для ускорения работы приложения.
- Авторизация и сохранение данных учетных записей для каждой платформы.
- Очистка кэша и массовая загрузка изображений с прогресс-баром.
- Возможность читать книги прямо из приложения (через внешний модуль `reader`).
- Удобный интерфейс на основе библиотеки `PySimpleGUI`.

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Azaki21421/SyncManager
   cd SyncManager
   ```
2. Убедитесь, что у вас установлен Python 3.8 или новее.

3. Установите зависимости:

```bash
pip install -r requirements.txt
```
4. Создайте директорию для кеша изображений, если она не создана автоматически:

```bash
mkdir image_cache
```

5. Убедитесь, что файл базы данных (database.db) находится в родительской директории проекта.


## Запуск
1. Запустите приложение:

```bash
python main.py
```
2. Используйте вкладки для навигации по доступным ранобэ.

## Использование
### Главный интерфейс
- Вкладки: Переключайтесь между различными источниками ранобэ.
- Список книг: Выберите книгу, чтобы посмотреть подробную информацию, включая изображение, описание и главу.
## Настройки
- Нажмите на значок "⚙" для входа в меню настроек.
- Возможности:
  - Авторизация для каждого сервиса.
  - Сохранение учетных данных.
  - Очистка кэша изображений.
  - Массовая загрузка изображений с прогресс-баром.
### Чтение книг
- Выберите книгу и нажмите кнопку Читать, чтобы открыть ее в модуле чтения.

## Зависимости
- `PySimpleGUI`: Для создания пользовательского интерфейса.
- `Pillow`: Для работы с изображениями.
- `requests`: Для загрузки данных из интернета.
- `beautifulsoup4`: Для парсинга HTML.
- `sqlite3`: Для работы с базой данных.
- Дополнительные модули:
  - `app_extension`
  - `ranoberf_next`
  - `ranobehub_nex`
  - `rulate_next`
  - `bd`

## Структура проекта
- `main.py`: Главный файл приложения.
- `app_extension.py`: Расширение для обработки чтения.
- `bd.py`: Модуль для работы с базой данных.
- `ranoberf_next.py`, `ranobehub_nex.py`, `rulate_next.py`: Модули для парсинга различных сервисов.
- `image_cache/`: Директория для сохранения кешированных изображений.

## Будущие улучшения
- Добавление новых платформ для работы с ранобэ.
- Оптимизация загрузки изображений.
- Расширение функционала модуля чтения.


