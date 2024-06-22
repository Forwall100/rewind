# Rewind ⬅️📽️

Rewind - это приложение для Linux, которое периодически делает снимки экрана вашего компьютера, распознает текст на этих снимках и сохраняет результаты в базу данных. В комплекте идет приложение для поиска по прошлым снимкам экрана и сервис, который работает в фоне, делая снимки экрана и распознавая текст на них.

## Поиск по тексту
![Screenshot from 2024-06-23 01-02-49](https://github.com/Forwall100/rewind/assets/78537089/79e7438b-d743-4374-a759-cce130210e9c)

## Таймлайн
![Screenshot from 2024-06-23 01-03-37](https://github.com/Forwall100/rewind/assets/78537089/27d37ca5-5b9c-48e4-b40c-1651711dc9de)

## Возможности 🚀

- **Автоматическое создание снимков экрана**: Делает снимки экрана с заданной периодичностью.
- **Распознавание текста**: Использует Tesseract OCR для извлечения текста из снимков экрана.
- **Поиск по тексту**: Сохраняет снимки экрана и извлеченный текст в базе данных SQLite.
- **Консольное приложение**: Позволяет искать по снимкам экрана в консоли.

## Установка 🛠️

Для установки Rewind на Arch Linux выполните следующие шаги:

1. **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/Forwall100/rewind.git
    cd rewind
    ```

2. **Запустите скрипт установки:**

    ```bash
    ./setup.sh
    ```

    Этот скрипт выполнит:
    - Установку необходимых зависимостей.
    - Сборку и установку пакета.
    - Включение и запуск службы Rewind для создания снимков экрана.

## Использование 🎮

### Запуск

Для запуска клиентского приложения Rewind выполните:

```bash
rewind
```

Это откроет консольное приложение, где вы сможете искать снимки экрана по тексту или времени их создания.

### Навигация в клиентском интерфейсе

- **Поиск**: Введите ваш запрос и используйте стрелочки для выбора нужного скриншота.
- **Режим временной шкалы**: Нажмите `Tab` для переключения режима временной шкалы. Используйте стрелочки влево и вправо для навигации по разным временным меткам.
- **Открыть изображение**: Нажмите `Enter` для открытия выбранного снимка экрана.
- **Выход**: Нажмите `Esc` для выхода из приложения.

## Хранение данных 💾

Rewind хранит свои данные в базе данных SQLite, расположенной по пути `~/.config/rewind/screenshots.db`. Снимки экрана сохраняются в виде бинарных данных, а текст, извлеченный из них, сохраняется в виде простого текста. Никакой безопасности)))

## Конфигурация ⚙️

Файл конфигурации расположен по пути `~/.config/rewind/config.yaml`. Вы можете настроить следующие параметры:

- **languages**: Языки для распознавания текста. По умолчанию `eng+rus`. Несколько языков указываются через '+'.
- **max_db_size_mb**: Максимальный размер базы данных в мегабайтах. По умолчанию `20000`.
- **screenshot_period_sec**: Период между снимками экрана в секундах. По умолчанию `30`.

### Пример `config.yaml`

```yaml
languages: "eng+rus"
max_db_size_mb: 20000
screenshot_period_sec: 30
```

## Служба Systemd 🔄

Фоновая служба управляется systemd. Файл службы `rewind-screenshot.service` установлен в `/usr/lib/systemd/user/`.

Для ручного запуска или остановки службы используйте:

```bash
systemctl --user start rewind-screenshot.service
systemctl --user stop rewind-screenshot.service
```

Для включения службы при входе в систему:

```bash
systemctl --user enable rewind-screenshot.service
```

## Зависимости 📦

Rewind зависит от следующих пакетов:

- `python`
- `python-pillow`
- `python-pytesseract`
- `python-yaml`
- `tesseract`
- `tesseract-data-eng`
- `tesseract-data-rus`
- `grim` (для Wayland)
- `scrot` (для X11)

Эти зависимости автоматически устанавливаются в процессе настройки. Для добавления новых языков OCR необходимо установить соответствующие пакеты tesseract-data-[langcode] и отредактировать конфиг.

## Удаление 🗑️

Для удаления Rewind выполните следующие шаги:

1. **Остановите и отключите службу:**

    ```bash
    systemctl --user stop rewind-screenshot.service
    systemctl --user disable rewind-screenshot.service
    ```

2. **Удалите установленные файлы:**

    ```bash
    sudo rm /usr/bin/rewind
    sudo rm /usr/lib/systemd/user/rewind-screenshot.service
    sudo rm -rf ~/.config/rewind
    ```

3. **Удалите пакет**

    ```bash
    sudo pacman -R rewind
    ```
