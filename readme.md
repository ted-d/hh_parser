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
много оьращений к апи хх.ру , было много мусорных вакансий,
а так же поиск длился очень долго, сейчас , разом получаю json
и фильтрую его  уже в коде , а после лью в бд
быстро и удобно . 

Просмотр вакансий:

```bash
python view_vacancies.py
```
## Структура проекта
```bash
q.py - основной парсер

view_vacancies.py - просмотр и фильтрация вакансий

config.py - настройки и конфигурация

requirements.txt - зависимости
```
## База данных
Перед первым запуском создайте таблицу:

```sql
DROP TABLE IF EXISTS vacancies;

-- Создаем новую таблицу с полными полями
CREATE TABLE vacancies (
    id SERIAL PRIMARY KEY,
    hh_id INTEGER UNIQUE,
    name VARCHAR(500),
    company VARCHAR(255),
    salary_from INTEGER,
    salary_to INTEGER,
    url VARCHAR(500),
    skills TEXT,
    description TEXT,
    category VARCHAR(50),
    relevance_score INTEGER DEFAULT 0,
    work_format VARCHAR(20),        -- NEW: remote/hybrid/office
    city VARCHAR(100),              -- NEW: город вакансии
    created_date TIMESTAMP DEFAULT NOW(),
    responded BOOLEAN DEFAULT FALSE
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_vacancies_date ON vacancies(created_date);
CREATE INDEX IF NOT EXISTS idx_vacancies_category ON vacancies(category);
CREATE INDEX IF NOT EXISTS idx_vacancies_score ON vacancies(relevance_score);
CREATE INDEX IF NOT EXISTS idx_vacancies_salary ON vacancies(salary_from, salary_to);
CREATE INDEX IF NOT EXISTS idx_vacancies_work_format ON vacancies(work_format);  -- NEW
CREATE INDEX IF NOT EXISTS idx_vacancies_city ON vacancies(city);                -- NEW
```
# Лицензия
Dmitry Tychinkin



И файл `requirements.txt`:

```txt
requests==2.31.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
```


