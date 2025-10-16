import requests
import psycopg2
import time
import re
from datetime import datetime, timedelta
from config import DB_CONFIG, KEYWORDS, GEO_CONFIG

class HHParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH-Parser/1.0',
            'Accept': 'application/json'
        })
    
    def clean_text(self, text):
        """Простая и надежная очистка через encode/decode"""
        if not text:
            return ""
        
        try:
            # Преобразуем в байты и обратно, игнорируя ошибки
            cleaned_text = text.encode('utf-8', 'ignore').decode('utf-8')
            
            # Дополнительно убираем оставшиеся проблемные символы
            cleaned_text = re.sub(r'[^\w\s\.\,\-\+\!\?\:\;\(\)\"\']', '', cleaned_text)
            
            return cleaned_text.strip()
            
        except:
            return ""
    
    def clean_html_tags(self, text):
        """Очистка текста от HTML тегов - с обработкой битых тегов"""
        if not text:
            return ""
        
        # Шаг 1: Заменяем "битые" теги вроде li> на нормальные <li>
        text = re.sub(r'(\w+)>', r'<\1>', text)
        
        # Шаг 2: Удаляем ВСЕ HTML теги
        clean_text = re.sub(r'</?[^>]*>', '', text)
        
        # Шаг 3: Заменяем HTML сущности
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', 
            '&gt;': '>', '&quot;': '"', '&apos;': "'"
        }
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
        # Шаг 4: Убираем множественные пробелы и переносы
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
    
    def extract_skills_from_text(self, text):
        """Извлечение навыков из текста"""
        if not text:
            return "не указаны"
        
        text_lower = text.lower()
        tech_keywords = [
            'python', 'sql', 'excel', 'n8n', 'make.com', 'zapier', 'airflow', 
            'power bi', 'tableau', 'superset', 'metabase', 'vba', 'pandas',
            'numpy', 'etl', 'api', 'docker', 'git', 'postgresql', 'mysql',
            'selenium', 'postman', 'jira', 'confluence'
        ]
        
        found_skills = []
        for keyword in tech_keywords:
            if keyword in text_lower:
                found_skills.append(keyword)
        
        return ', '.join(found_skills) if found_skills else 'не указаны'
    
    def check_work_format(self, vacancy_item, vacancy_detail):
        """ДЕБАГ ВЕРСИЯ - посмотрим что на самом деле в API"""
        schedule = vacancy_item.get('schedule', {})
        schedule_id = schedule.get('id')
        schedule_name = schedule.get('name', '')
        
        print(f"🎯 ДЕБАГ Формата: {vacancy_item['name'][:30]}...")
        print(f"   📅 Schedule ID: '{schedule_id}'")
        print(f"   📅 Schedule Name: '{schedule_name}'")
        
        # Простая логика - берем ТОЛЬКО из schedule.id
        if schedule_id == 'remote':
            result = 'remote'
        elif schedule_id in ['fullDay', 'shift', 'flexible']:
            result = 'office'
        else:
            result = 'unknown'
        
        print(f"   ✅ Результат: {result}")
        print("-" * 40)
        
        return result
    
    def is_suitable_location(self, work_format, area_id):
        """Упрощенная версия для теста"""
        is_tyumen = area_id == GEO_CONFIG['preferred_city_id']
        
        print(f"📍 Гео-фильтр: Тюмень={is_tyumen}, Формат={work_format}")
        
        # Тюмень - ВСЕ форматы
        if is_tyumen:
            print("   ✅ Тюмень - подходит любой формат")
            return True
        
        # Другие города - только удаленка
        if work_format == 'remote':
            print("   ✅ Другой город - подходит remote")
            return True
        else:
            print(f"   ❌ Другой город - НЕ подходит {work_format}")
            return False
        
    def parse_salary(self, salary_data):
        """Корректная обработка зарплаты"""
        if not salary_data:
            return None, None
        
        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        
        # Конвертируем в рубли если указано в другой валюте
        if salary_data.get('currency') != 'RUR':
            if salary_from:
                salary_from = salary_from * 70
            if salary_to:
                salary_to = salary_to * 70
        
        return salary_from, salary_to
    
    def categorize_vacancy(self, vacancy):
        """Расширенная категоризация вакансий"""
        title = vacancy['name'].lower()
        desc = vacancy.get('description', '').lower()
        skills = vacancy.get('skills', '').lower()
        
        text = f"{title} {desc} {skills}"
        
        categories_priority = [
            {
                'name': 'automation',
                'keywords': ['n8n', 'make.com', 'zapier', 'rpa', 'workflow', 'интеграц', 'автоматизац']
            },
            {
                'name': 'data_engineering', 
                'keywords': ['airflow', 'etl', 'data pipeline', 'dbt', 'data engineer', 'data engineering']
            },
            {
                'name': 'bi',
                'keywords': ['power bi', 'tableau', 'superset', 'metabase', 'bi analyst', 'дашборд', 'dashboard']
            },
            {
                'name': 'python_sql',
                'keywords': ['python', 'sql', 'pandas', 'numpy', 'data analysis', 'scripting']
            },
            {
                'name': 'excel',
                'keywords': [
                    'excel', 'vba', 'макрос', 'power query', 'сводн', 'macro',
                    'pivot table', 'pivot', 'сводная таблица', 'сводные таблицы',
                    'vlookup', 'впр', 'xlookup', 'index match', 'поискправ',
                    'power pivot', 'get transform', 'фильтры', 'advanced filter',
                    'условное форматирование', 'conditional formatting',
                    'диаграмма', 'chart', 'график', 'sparkline',
                    'data analysis', 'анализ данных', 'excel аналитик',
                    'формулы'
                ]
            },
            {
                'name': 'documentation',
                'keywords': [
                    'confluence', 'документац', 'техническ', 'инструкц', 'руководств',
                    'technical writer', 'технический писатель', 'документация',
                    'база знаний', 'knowledge base', 'мануал', 'manual', 
                    'техписатель', 'тех писатель', 'write documentation'
                ]
            },
            {
                'name': 'qa_testing',
                'keywords': [
                    'qa', 'quality assurance', 'тестировщик', 'тестирование', 'testing',
                    'manual testing', 'ручное тестирование', 'автоматизация тестирования',
                    'test automation', 'selenium', 'postman', 'api testing', 'тестирование api',
                    'functional testing', 'функциональное тестирование', 'regression testing',
                    'регрессионное тестирование', 'test case', 'тест кейс', 'test plan'
                    , 'bug report', 'баг репорт',  'jira', 'testrail',
                    'qc', 'quality control', 'контроль качества', 'junior qa', 'trainee qa',
                    'qa engineer', 'инженер по тестированию', 'software tester'
                ]
            },
            {
                'name':'archivist', 
                'keywords': ['архивариус', 'архив', 'делопроизводитель', 'делопроизводство', 'канцелярия']
            }
        ]
        
        for category in categories_priority:
            for keyword in category['keywords']:
                if keyword in text:
                    return category['name']
        
        return 'other'
    
    def calculate_relevance(self, vacancy, work_format):
        """Расчет релевантности с учетом локации"""
        score = 0
        title = vacancy['name'].lower()
        desc = vacancy.get('description', '').lower()
        skills = vacancy.get('skills', '').lower()
        
        text = f"{title} {desc} {skills}"
        
        high_priority = ['n8n', 'airflow', 'superset', 'power bi', 'tableau', 'etl', 'dbt']
        medium_priority = ['python', 'sql', 'pandas', 'vba', 'excel', 'dashboard']
        low_priority = ['data', 'analysis', 'автоматизац', 'анализ']
        
        for keyword in high_priority:
            if keyword in text:
                score += 3
        
        for keyword in medium_priority:
            if keyword in text:
                score += 2
                
        for keyword in low_priority:
            if keyword in text:
                score += 1
        
        # Бонус за указание зарплаты
        if vacancy.get('salary_from') or vacancy.get('salary_to'):
            score += 2
        
        # Бонус за подходящий формат работы
        if work_format == 'remote':
            score += 3
        elif work_format == 'hybrid':
            score += 2
        elif work_format == 'office':
            score += 1
            
        return min(score, 10)
    
    def get_vacancy_details(self, vacancy_id):
        """Получение детальной информации о вакансии"""
        try:
            response = self.session.get(
                f"https://api.hh.ru/vacancies/{vacancy_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Ошибка получения деталей вакансии {vacancy_id}: {e}")
        return {}
    
    def get_hh_vacancies(self):
        """Основной метод получения вакансий - РАЗДЕЛЬНЫЙ поиск"""
        url = "https://api.hh.ru/vacancies"
        all_vacancies = []
        
        # 1. СНАЧАЛА ИЩЕМ ПО ТЮМЕНИ (все форматы работы)
        print("🎯 ЭТАП 1: ПОИСК ПО ТЮМЕНИ (офис/гибрид/удаленка)")
        print("=" * 50)
        
        for keyword in KEYWORDS:
            print(f"🔍 Тюмень: {keyword}")
            
            page = 0
            total_pages = 1
            
            while page < total_pages:
                params = {
                    'text': keyword,
                    'area': 1410,  # Только Тюмень!
                    'per_page': 20,
                    'page': page,
                    'order_by': 'publication_time',
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=10)
                    data = response.json()
                    
                    total_pages = min(data.get('pages', 1), 2)  # Максимум 2 страницы
                    found = data.get('found', 0)
                    
                    if page == 0:
                        print(f"   📨 Найдено в Тюмени: {found}")
                        print(f"   📄 Страниц для обработки: {total_pages}")
                    
                    print(f"   📖 Обрабатывается страница {page + 1}/{total_pages}")
                    
                    page_vacancies = 0
                    for item in data.get('items', []):
                        # Пропускаем старые вакансии
                        published = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                        if datetime.now(published.tzinfo) - published > timedelta(days=10):
                            continue
                        
                        # ФИЛЬТР ПО ОПЫТУ
                        experience = item.get('experience', {})
                        experience_id = experience.get('id')
                        if experience_id not in ['noExperience', 'between1And3']:
                            continue
                        
                        # Получаем детали
                        vacancy_detail = self.get_vacancy_details(item['id'])
                        time.sleep(0.1)
                        
                        # Определяем формат работы
                        work_format = self.check_work_format(item, vacancy_detail)
                        
                        # Для Тюмени ВСЕ форматы подходят - сохраняем
                        salary_from, salary_to = self.parse_salary(item.get('salary'))
                        
                        # УЛУЧШЕННАЯ ОБРАБОТКА SKILLS И DESCRIPTION
                        skills_from_api = [s['name'] for s in item.get('key_skills', [])]
                        if skills_from_api:
                            cleaned_skills = ', '.join(skills_from_api)
                        else:
                            # Если API не дало skills, извлекаем из описания
                            cleaned_skills = self.extract_skills_from_text(vacancy_detail.get('description', ''))
                        
                        # Очищаем description от HTML тегов
                        raw_description = vacancy_detail.get('description', '')
                        cleaned_description = self.clean_html_tags(raw_description)[:1500]
                        
                        vacancy = {
                            'hh_id': int(item['id']),
                            'name': self.clean_text(item['name']),
                            'company': self.clean_text(item['employer']['name']),
                            'salary_from': salary_from,
                            'salary_to': salary_to,
                            'url': item['alternate_url'],
                            'skills': cleaned_skills,
                            'description': cleaned_description,
                            'work_format': work_format,
                            'city': item.get('area', {}).get('name', 'Тюмень')
                        }
                        
                        vacancy['category'] = self.categorize_vacancy(vacancy)
                        vacancy['relevance_score'] = self.calculate_relevance(vacancy, work_format)
                        
                        all_vacancies.append(vacancy)
                        page_vacancies += 1
                        print(f"   ✅ Тюмень: {vacancy['name'][:40]}... | {work_format}")
                    
                    print(f"   📊 На странице {page + 1} добавлено: {page_vacancies} вакансий")
                    page += 1
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"❌ Ошибка при поиске в Тюмени {keyword}, страница {page}: {e}")
                    break
        
        # 2. ПОТОМ ИЩЕМ ПО РОССИИ (только удаленка, без Тюмени)
        print("\n🎯 ЭТАП 2: ПОИСК ПО РОССИИ (только удаленка, без Тюмени)")
        print("=" * 50)
        
        for keyword in KEYWORDS:
            print(f"🔍 Россия (без Тюмени): {keyword}")
            
            page = 0
            total_pages = 1
            
            while page < total_pages:
                params = {
                    'text': f'{keyword} !Тюмень',  # ❌ Исключаем Тюмень
                    'area': 113,  # Вся Россия
                    'per_page': 30,
                    'page': page,
                    'order_by': 'publication_time',
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=10)
                    data = response.json()
                    
                    total_pages = min(data.get('pages', 1), 2)  # Максимум 2 страницы
                    found = data.get('found', 0)
                    
                    if page == 0:
                        print(f"   📨 Найдено в России (без Тюмени): {found}")
                        print(f"   📄 Страниц для обработки: {total_pages}")
                    
                    print(f"   📖 Обрабатывается страница {page + 1}/{total_pages}")
                    
                    page_vacancies = 0
                    for item in data.get('items', []):
                        # Пропускаем старые вакансии
                        published = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                        if datetime.now(published.tzinfo) - published > timedelta(days=5):
                            continue
                        
                        # ФИЛЬТР ПО ОПЫТУ
                        experience = item.get('experience', {})
                        experience_id = experience.get('id')
                        if experience_id not in ['noExperience', 'between1And3']:
                            continue
                        
                        # Получаем детали
                        vacancy_detail = self.get_vacancy_details(item['id'])
                        time.sleep(0.1)
                        
                        # Определяем формат работы
                        work_format = self.check_work_format(item, vacancy_detail)
                        
                        # Фильтруем по локации (только удаленка для других городов)
                        if work_format != 'remote':
                            continue
                        
                        # Обрабатываем и сохраняем удаленку
                        salary_from, salary_to = self.parse_salary(item.get('salary'))
                        
                        # УЛУЧШЕННАЯ ОБРАБОТКА SKILLS И DESCRIPTION
                        skills_from_api = [s['name'] for s in item.get('key_skills', [])]
                        if skills_from_api:
                            cleaned_skills = ', '.join(skills_from_api)
                        else:
                            cleaned_skills = self.extract_skills_from_text(vacancy_detail.get('description', ''))
                        
                        # Очищаем description от HTML тегов
                        raw_description = vacancy_detail.get('description', '')
                        cleaned_description = self.clean_html_tags(raw_description)[:1500]
                        
                        vacancy = {
                            'hh_id': int(item['id']),
                            'name': self.clean_text(item['name']),
                            'company': self.clean_text(item['employer']['name']),
                            'salary_from': salary_from,
                            'salary_to': salary_to,
                            'url': item['alternate_url'],
                            'skills': cleaned_skills,
                            'description': cleaned_description,
                            'work_format': work_format,
                            'city': item.get('area', {}).get('name', 'Не указан')
                        }
                        
                        vacancy['category'] = self.categorize_vacancy(vacancy)
                        vacancy['relevance_score'] = self.calculate_relevance(vacancy, work_format)
                        
                        all_vacancies.append(vacancy)
                        page_vacancies += 1
                        print(f"   ✅ Россия: {vacancy['name'][:40]}... | {work_format}")
                    
                    print(f"   📊 На странице {page + 1} добавлено: {page_vacancies} вакансий")
                    page += 1
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"❌ Ошибка при поиске в России {keyword}, страница {page}: {e}")
                    break
        
        return all_vacancies

def save_to_db(vacancies):
    """Сохранение вакансий в базу данных"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    error_count = 0
    
    for vac in vacancies:
        try:
            cursor.execute("""
                INSERT INTO vacancies 
                (hh_id, name, company, salary_from, salary_to, url, skills, 
                 description, category, relevance_score, work_format, city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hh_id) DO NOTHING
                RETURNING id
            """, (
                vac['hh_id'], vac['name'], vac['company'], vac['salary_from'], 
                vac['salary_to'], vac['url'], vac['skills'], vac['description'],
                vac['category'], vac['relevance_score'], vac['work_format'], vac['city']
            ))
            
            if cursor.fetchone():
                new_count += 1
            else:
                duplicate_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"❌ Ошибка сохранения вакансии {vac['hh_id']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return new_count, duplicate_count, error_count

if __name__ == "__main__":
    print(f"🕒 {datetime.now()} - Запуск парсера HH.ru")
    print(f"📍 Гео-фильтр: Тюмень - любой формат, другие города - только удаленка")
    print(f"💼 Опыт: без опыта или 1-3 года")
    print("=" * 60)
    
    parser = HHParser()
    vacancies = parser.get_hh_vacancies()
    
    print(f"🎯 Найдено подходящих вакансий: {len(vacancies)}")
    
    if vacancies:
        new_count, duplicate_count, error_count = save_to_db(vacancies)
        print(f"💾 Сохранено: новых {new_count}, дубликатов {duplicate_count}, ошибок {error_count}")
        
        # Статистика по форматам работы
        formats = {}
        for vac in vacancies:
            fmt = vac['work_format']
            formats[fmt] = formats.get(fmt, 0) + 1
        
        print("\n📊 Статистика по форматам работы:")
        for fmt, count in formats.items():
            print(f"  {fmt}: {count} вакансий")
    else:
        print("❌ Подходящих вакансий не найдено")