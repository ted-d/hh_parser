-- Удаляем старую таблицу если существует
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