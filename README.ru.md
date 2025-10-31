# Compass On‑premise Installer

`easy-install.py` подготавливает сервер к развертыванию Compass On‑premise: удаляет AppArmor, проверяет ресурсы, устанавливает системные зависимости, выпускает сертификаты и запускает основной инсталлятор `install.py`. Можно указать домен (`--domain example.org`) и включить выпуск Let’s Encrypt (`--le`). Если домен не задан, будет использован IP сервера, а TLS выпустится локальным центром Compass.

## Быстрый запуск

```bash
sudo apt update && sudo apt install -y git python3 python3-venv
git clone https://github.com/getCompass/onpremise-installer.git
cd onpremise-installer
sudo python3 script/easy-install.py \
  --yes \
  --domain example.org \
  --le \
  --admin-email admin@example.org
```

> При желании можно не указывать `--domain` — тогда конфигурация будет заполняться по IP и автоматически выпустится локальный сертификат Compass. Аналогично, флаг `--le` необязателен: без него будет создана локальная цепочка CA.

Скрипт:

1. Остановит и удалит `AppArmor` (при необходимости).
2. Проверит CPU/RAM/диск и IOPS.
3. Определит тип ОС и доустановит пакеты (nginx, docker, certbot, fio и т.д.).
4. Включит Docker + Docker Swarm, создаст виртуальное окружение и Python-зависимости.
5. Сгенерирует шаблонные конфигурационные файлы в `configs/`.
6. Выпустит сертификат Let’s Encrypt или локальный (с промежуточным CA).
7. Применит обязательные патчи YAML.
8. Запустит `install.py --confirm-all` (если не указан `--skip-install`).

## Параметры `easy-install.py`

| Опция | Описание |
| --- | --- |
| `-y, --yes` | Автоматически отвечать «Да» на все подтверждения. |
| `-l, --lang {ru,en}` | Язык сообщений (по умолчанию ru). |
| `-d, --domain <FQDN>` | Домен для `global.yaml` и сертификатов. |
| `--le` | Выпустить Let’s Encrypt сертификат (требует `--domain`). |
| `--root-mount <PATH>` | Каталог данных приложения (по умолчанию `/opt/compass_data`). |
| `--admin-email <EMAIL>` | E-mail администратора (попадает в `team.yaml`). |
| `--admin-password <PWD>` | Пароль администратора (иначе будет сгенерирован). |
| `--skip-checks` | Пропустить проверки ресурсов и IOPS. |
| `--skip-bench` | Пропустить только IOPS-бенчмарк. |
| `--bench-runtime <SECONDS>` | Длительность каждого теста fio (по умолчанию 20 сек). |
| `--skip-install` | Не запускать `install.py` после подготовки. |
| `--log-file <PATH>` | Путь к журналу (`logs/easy-install_<timestamp>.log` по умолчанию). |
| `--dry-run` | Только показать план действий без изменений. |
| `--verbose` | Подробный вывод. |

## После выполнения

- Итоговая сводка выводится в консоль и журнал (`summary.*`).
- Конфигурационные файлы лежат в `configs/`. Для расширенной настройки используйте [официальную документацию](https://doc-onpremise.getcompass.ru/information.html).
- Сертификаты размещаются в `/etc/nginx/ssl/` (локальный и Let’s Encrypt). При необходимости замените их на собственные.
- Если `install.py` был пропущен (флаг или отказ), запустите его вручную:

```bash
sudo python3 script/install.py --confirm-all
```

## Дополнительная информация

Полное руководство: [doc-onpremise.getcompass.ru](https://doc-onpremise.getcompass.ru/information.html) — включает подготовку окружения, подключение SMTP/SMS/SSO, работу с Captcha, отказоустойчивость и др.

За поддержкой обращайтесь в [пространство On-premise](https://getcompass.com/join/wlSjdBJd/), [Telegram](https://t.me/getcompass) или на почту [support@getcompass.ru](mailto:support@getcompass.ru).
