# Compass On‑premise Installer

`easy-install.py` готовит сервер к развертыванию Compass On‑premise: удаляет AppArmor при необходимости, проверяет ресурсы, ставит системные зависимости, выпускает сертификаты и запускает основной установщик `install.py`. При желании можно указать домен (`--domain`) и включить Let’s Encrypt (`--le`); без домена используется IP-адрес и генерируется локальный сертификат Compass.

## Обзор

1. Проверка версии Python и повторный запуск при необходимости.
2. Отключение AppArmor.
3. Проверка CPU, RAM, диска и IOPS.
4. Определение ОС, установка недостающих пакетов (nginx, docker, fio и др.).
5. Настройка Docker + Swarm, создание виртуального окружения Python.
6. Генерация конфигураций `create_configs.py`.
7. Выпуск сертификатов Let’s Encrypt или локального CA.
8. Применение YAML-патчей.
9. Запуск `install.py` (если не указан `--skip-install`).

## Требования

**Минимальное ПО:** установленный `python3`. Все остальные зависимости (`nginx`, `docker`, `fio`, `acme.sh`, `ruamel.yaml` и т.д.) скрипт поставит сам.

**Поддерживаемые ОС:**

- Debian-подобные: Debian 10+, Ubuntu 20.04+.
- RPM-совместимые: RedOS 8+, AlmaLinux 9.6+, МСВСфера 9.6+, ALT Linux 11.0+, Fedora 36+.

**Аппаратные требования (как в проверках скрипта):**

- CPU: от 8 потоков (vCPU).
- RAM: от 16 Гбайт.
- Диск: от 30 Гбайт свободного места на корне данных и Docker data-root.

## Быстрый запуск

```bash
sudo apt update && sudo apt install -y git python3 python3-venv
git clone git@github.com:compass-onpremise/onpremise-installer-easy-install.git
cd onpremise-installer-easy-install
sudo python3 script/easy-install.py \
  --yes \
  --domain example.org \
  --le \
  --admin-email admin@example.org
```

> Параметры `--domain` и `--le` необязательны. Без `--le` будет выпущен локальный сертификат через встроенный промежуточный CA; без домена настройки выполняются по IP.

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
- Конфигурации появляются в `configs/`. При ручной настройке либо повторном запуске используйте эти файлы.
- Сертификаты находятся в `/etc/nginx/ssl/`.
- Если `install.py` пропущен, запустите его вручную:

```bash
sudo python3 script/install.py --confirm-all
```

## Ручная установка и дополнительная документация

- Подробные инструкции по развёртыванию и настройке: [doc-onpremise.getcompass.ru](https://doc-onpremise.getcompass.ru/information.html).
- Если требуется ручная установка без `easy-install.py`, следуйте разделу «Подготовка к развертыванию» в документации по ссылке выше.

Поддержка: [пространство On-premise](https://getcompass.com/join/wlSjdBJd/), [Telegram](https://t.me/getcompass) или [support@getcompass.ru](mailto:support@getcompass.ru).
