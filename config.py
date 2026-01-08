import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'hh_parser'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

# КЛЮЧЕВЫЕ СЛОВА ДЛЯ ПОИСКА В API
KEYWORDS = [
    # Automation & RPA
    'n8n', 'make.com', 'zapier', 'automation', 'rpa', 'workflow', 'интеграц', 'автоматизац',
    
    # Data Engineering & ETL
    'airflow', 'etl', 'data pipeline', 'dbt', 'data engineer', 'data engineering',
    'data processing', 'data transformation',
    
    # BI & Dashboards
    'power bi', 'tableau', 'superset', 'metabase', 'bi analyst', 'business intelligence',
    'дашборд', 'визуализац', 'data visualization', 'bi developer', 'bi разработчик',
    
    # Python/SQL & Scripting
    'python', 'sql', 'data analysis', 'аналитик', 'pandas', 'numpy', 'scripting',
    'data script', 'data analyst',
    
    # Excel & Office Automation
    'excel', 'vba', 'макрос', 'power query', 'сводн', 'office automation',
    'pivot table', 'сводная таблица', 'vlookup', 'впр', 'xlookup', 'index match',
    'power pivot', 'advanced filter', 'условное форматирование',
    'диаграмма', 'chart', 'график', 'sparkline', 'формулы',
    
    # Documentation & Technical Writing
    'confluence', 'документац', 'technical writer', 'технический писатель', 'документация',
    'база знаний', 'knowledge base', 'мануал', 'manual', 'описание процесс',
    
    # QA & Testing
    'qa', 'quality assurance', 'тестировщик', 'тестирование', 'testing',
    'manual testing', 'ручное тестирование', 'автоматизация тестирования',
    'test automation', 'selenium', 'postman', 'api testing', 'тестирование api',
    'functional testing', 'функциональное тестирование', 'test case', 'тест кейс',
    
    # NEW: Бизнес-аналитика
    'бизнес-аналитик', 'бизнес аналитик', 'менеджер по данным', 
    'data manager', 'business analyst', 'аналитик данных',
    'powerpoint', 'управленческ', 'отчетност', 'презентац',
    
    # NEW: Архивариус и делопроизводитель
    'архивариус', 'архив', 'делопроизводитель', 'делопроизводство', 'канцелярия',
    'секретарь', 'документооборот', 'архивное дело',
    
    # NEW: Оператор данных
    'оператор данных', 'data entry', 'ввод данных', 'обработк данных', 
    'оператор баз данных', 'data operator',
    
    # Для Тюмени (общие)
    '1с', 'бухгалтер', 'специалист', 'оператор', 'контент', 'копирайтер',
    'верстальщик', 'frontend', 'backend', 'разработчик', 'системный администратор',
    'сетевой инженер', 'техподдержка', 'hr', 'производство', 'инженер', 'технолог', 'конструктор'
]

# КАТЕГОРИИ ДЛЯ КЛАССИФИКАЦИИ (приоритет по порядку)
CATEGORIES = {
    'automation': {
        'keywords': ['n8n', 'make.com', 'zapier', 'rpa', 'workflow', 'интеграц', 'автоматизац'],
        'priority': 1
    },
    'data_engineering': {
        'keywords': ['airflow', 'etl', 'data pipeline', 'dbt', 'data engineer'],
        'priority': 2
    },
    'bi': {
        'keywords': [
            'power bi', 'tableau', 'superset', 'metabase', 'qlik', 
            'дашборд', 'dashboard', 'bi developer', 'bi разработчик',
            'bi analyst', 'bi аналитик', 'business intelligence',
            'визуализац данных', 'data visualization', 'отчетность'
        ],
        'priority': 3
    },
    'business_analysis': {
        'keywords': [
            'бизнес-аналитик', 'бизнес аналитик', 'менеджер по данным',
            'business analyst', 'data manager', 'аналитик данных',
            'powerpoint', 'управленческ', 'отчетност', 'презентац',
            'сводн', 'power point', 'pdf отчет'
        ],
        'priority': 4,
        'exclude': ['1с', 'бухгалтер', 'оператор']
    },
    'qa_testing': {
        'keywords': ['qa', 'тестировщик', 'тестирование', 'selenium', 'test automation'],
        'priority': 5
    },
    'documentation': {
        'keywords': ['technical writer', 'технический писатель', 'confluence', 'документац'],
        'priority': 6
    },
    'archivist': {
        'keywords': ['архивариус', 'архив', 'делопроизводитель', 'делопроизводство', 'канцелярия'],
        'priority': 7
    },
    'data_operator': {
        'keywords': ['оператор данных', 'data entry', 'ввод данных', 'обработк данных'],
        'priority': 8
    },
    'excel': {
        'keywords': ['excel', 'vba', 'макрос', 'power query', 'сводн'],
        'priority': 9,
        'exclude': ['python', 'sql', 'разработк', 'developer', 'программист']
    },
    'python_sql': {
        'keywords': ['python', 'sql', 'pandas', 'data analysis', 'аналитик'],
        'priority': 10
    }
}

GEO_CONFIG = {
    'preferred_city': 'Тюмень',
    'preferred_city_id': 1410,
    'remote_keywords': ['удален', 'remote', 'дистанцион', 'work from home', 'удалён'],
    'hybrid_keywords': ['гибрид', 'hybrid', 'частично удален', 'гибкий график']
}

EXPERIENCE_FILTER = {
    'allowed_experience': ['noExperience', 'between1And3'],
    'experience_keywords': ['нет опыта', 'без опыта', '1 год', '2 года', '3 года', '1-3 года']
}