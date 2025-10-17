# HH.ru Parser

Парсер вакансий с HH.ru с интеллектуальной фильтрацией по геолокации и формату работы.

## Особенности

- 📍 **Гео-фильтрация**: Тюмень - все форматы, другие города - только удаленка
- 💼 **Фильтр по опыту**: без опыта или 1-3 года  
- 🏷️ **Авто-категоризация**: автоматическое определение категории вакансии
- ⭐ **Система релевантности**: оценка вакансий по ключевым словам
- 💾 **PostgreSQL**: сохранение в базу данных

## Установка

1. Клонировать репозиторий:
```bash
git clone <url-репозитория>
cd hh-parser
```
2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настроить базу данных PostgreSQL

4. Создать файл .env с настройками:
```bash
DB_HOST=localhost
DB_NAME=hh_parser  
DB_USER=postgres
DB_PASSWORD=password
DB_PORT=5432
```

# Использование
Запуск парсера:
```bash
python q.py

```
почему q-quick быстрый поиск , изначально я делал 
много оьращений к апи хх.ру , было много мусорных вакансий 
а так де поиск длился очень долго, сейчас , разом получаю json
и фильтруб уже в коде и лью в бд
быстро и удобно . 
Просмотр вакансий:

```bash
python view_vacancies.py
```
## Структура проекта
```bash
hh_parser.py - основной парсер

view_vacancies.py - просмотр и фильтрация вакансий

config.py - настройки и конфигурация

requirements.txt - зависимости
```
## База данных
Перед первым запуском создайте таблицу:

```sql
CREATE TABLE vacancies (
    id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE,
    name TEXT,
    company TEXT,
    salary_from INTEGER,
    salary_to INTEGER,
    url TEXT,
    skills TEXT,
    description TEXT,
    category VARCHAR(50),
    relevance_score INTEGER,
    work_format VARCHAR(20),
    city VARCHAR(100),
    created_date TIMESTAMP DEFAULT NOW()
);
```
# Лицензия
Dmitry Tychinkin



И файл `requirements.txt`:

```txt
requests==2.31.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
```


