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
            cleaned_text = text.encode('utf-8', 'ignore').decode('utf-8')
            cleaned_text = re.sub(r'[^\w\s\.\,\-\+\!\?\:\;\(\)\"\']', '', cleaned_text)
            return cleaned_text.strip()
        except:
            return ""
    def clean_text_safe(self, text, max_length=2000):
        """УЛЬТРА-безопасная очистка для БД"""
        if not text:
            return ""
        
        try:
            # Жесткая очистка - только буквы, цифры и базовые символы
            cleaned = re.sub(r'[^\w\s\.\,\-\+\!\?\(\)\:\;\@\#\%\&\=\*\\\/]', '', text)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()[:max_length]
        except:
            return text[:max_length] if text else "" 
    def clean_html_tags(self, text):
        """Очистка текста от HTML тегов"""
        if not text:
            return ""
        
        text = re.sub(r'(\w+)>', r'<\1>', text)
        clean_text = re.sub(r'</?[^>]*>', '', text)
        
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', 
            '&gt;': '>', '&quot;': '"', '&apos;': "'"
        }
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
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
        """Определяем формат работы"""
        schedule = vacancy_item.get('schedule', {})
        schedule_id = schedule.get('id')
        
        # Сначала проверяем schedule.id
        if schedule_id == 'remote':
            return 'remote'
        
        # Проверяем текст на удаленку
        name = vacancy_item.get('name', '').lower()
        desc = vacancy_detail.get('description', '').lower()
        text = f"{name} {desc}"
        
        remote_keywords = ['удален', 'remote', 'дистанцион', 'work from home', 'удалён']
        if any(keyword in text for keyword in remote_keywords):
            return 'remote'
        
        # Все остальное - офис (включая гибрид)
        return 'office'
    
    def parse_salary(self, salary_data):
        """Корректная обработка зарплаты"""
        if not salary_data:
            return None, None
        
        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        
        if salary_data.get('currency') != 'RUR':
            if salary_from:
                salary_from = salary_from * 70
            if salary_to:
                salary_to = salary_to * 70
        
        return salary_from, salary_to
    
    def categorize_vacancy(self, vacancy):
        """Категоризация на основе конфига с приоритетами"""
        title = vacancy['name'].lower()
        desc = vacancy.get('description', '').lower()
        skills = vacancy.get('skills', '').lower()
        
        text = f" {title} {desc} {skills} "
        
        from config import CATEGORIES
        sorted_categories = sorted(CATEGORIES.items(), key=lambda x: x[1]['priority'])
        
        for category_name, category_data in sorted_categories:
            keywords = category_data['keywords']
            
            has_keywords = any(f' {kw} ' in text for kw in keywords)
            
            if 'exclude' in category_data:
                has_exclude = any(f' {kw} ' in text for kw in category_data['exclude'])
                if has_keywords and not has_exclude:
                    return category_name
            else:
                if has_keywords:
                    return category_name
        
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
        """Загружаем ВСЕ вакансии одним запросом -> фильтруем на нашей стороне"""
        url = "https://api.hh.ru/vacancies"
        all_vacancies = []
        
        # ОДИН большой запрос - ВСЕ вакансии России
        params = {
            'text': 'python OR sql OR vba OR excel OR аналитик OR данные OR разработчик OR тестировщик OR 1с OR бухгалтер OR оператор OR специалист OR BI аналитик OR n8n OR Airflow OR superset ',  # Широкий охват
            'area': 113,  # Вся Россия
            'per_page': 100,  # Максимум на странице
            'page': 0,
            'period': 7,  # Только за последние 7 дней (свежие)
        }
        
        print("🔍 Загружаем ВСЕ подходящие вакансии России за 7 дней...")
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            
            found = data.get('found', 0)
            pages = data.get('pages', 1)
            
            print(f"📨 Найдено вакансий по запросу: {found}")
            print(f"📄 Страниц для обработки: {pages}")
            
            # Обрабатываем ВСЕ страницы
            for page in range(pages):
                if page > 0:  # Первую страницу уже загрузили
                    params['page'] = page
                    response = self.session.get(url, params=params, timeout=15)
                    data = response.json()
                
                print(f"📖 Обрабатывается страница {page + 1}/{pages}")
                
                page_count = 0
                for item in data.get('items', []):
                    try:
                        # Базовые данные
                        city = item.get('area', {}).get('name', 'Не указан')
                        vacancy_id = item['id']
                        
                        # 🔥 ФИЛЬТР 1: Формат работы
                        schedule_id = item.get('schedule', {}).get('id', '')
                        work_format = 'remote' if schedule_id == 'remote' else 'office'
                        
                        # ОСНОВНОЙ ФИЛЬТР: Тюмень - все, другие города - только удаленка
                        if city != 'Тюмень' and work_format != 'remote':
                            continue
                        
                        # 🔥 ФИЛЬТР 2: Опыт работы
                        experience_id = item.get('experience', {}).get('id', '')
                        if experience_id not in ['noExperience', 'between1And3']:
                            continue
                        
                        # 🔥 ФИЛЬТР 3: Ключевые слова в названии
                        name = item.get('name', '').lower()
                        
                        # Расширенный список профессий
                        target_keywords = [
                            'python', 'sql', 'excel', 'n8n', 'airflow', 'power bi', 'tableau',
                            'data', 'аналитик', 'анализ', 'данн', 'etl', 'dash', 'дашборд',
                            'qa', 'тестировщик', 'тестирование', 'testing', 
                            '1с', 'бухгалтер', 'оператор', 'специалист',
                            'архивариус', 'делопроизводитель', 'документац', 'архив',
                            'confluence', 'автоматизац', 'rpa', 'workflow',
                            'менеджер', 'администратор', 'координатор', 'помощник'
                        ]
                        
                        # Проверяем совпадение с любым ключевым словом
                        has_keyword = any(keyword in name for keyword in target_keywords)
                        if not has_keyword:
                            continue
                        
                        # 🔥 ВСЕ фильтры пройдены - сохраняем вакансию
                        
                        # Обработка зарплаты
                        salary_data = item.get('salary')
                        salary_from = None
                        salary_to = None
                        
                        if salary_data:
                            salary_from = salary_data.get('from')
                            salary_to = salary_data.get('to')
                            
                            if salary_data.get('currency') != 'RUR':
                                if salary_from:
                                    salary_from = salary_from * 70
                                if salary_to:
                                    salary_to = salary_to * 70
                        
                        # Получаем полное описание
                        vacancy_detail = self.get_vacancy_details(vacancy_id)
                        full_description = ""
                        
                        if vacancy_detail:
                            raw_description = vacancy_detail.get('description', '')
                            full_description = self.clean_html_tags(raw_description)[:2000]
                        
                        # Формируем вакансию
                        vacancy = {
                            'hh_id': int(vacancy_id),
                            'name': self.clean_text(item['name']),
                            'company': self.clean_text(item['employer']['name']),
                            'salary_from': salary_from,
                            'salary_to': salary_to,
                            'url': item['alternate_url'],
                            'skills': ', '.join([s['name'] for s in item.get('key_skills', [])]),
                            'description': full_description,
                            'work_format': work_format,
                            'city': city
                        }
                        
                        vacancy['category'] = self.categorize_vacancy(vacancy)
                        vacancy['relevance_score'] = self.calculate_relevance(vacancy, work_format)
                        
                        all_vacancies.append(vacancy)
                        page_count += 1
                        print(f"✅ {city}: {vacancy['name'][:50]}... | {work_format}")
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки вакансии: {e}")
                        continue
                
                print(f"📊 На странице {page + 1} добавлено: {page_count} вакансий")
                
                # Задержка между страницами
                if page < pages - 1:
                    time.sleep(0.5)
            
            print(f"\n🎯 ИТОГО найдено подходящих вакансий: {len(all_vacancies)}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
        
        return all_vacancies

def save_to_db(vacancies):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    error_count = 0
    
    parser = HHParser()  # создаем парсер для очистки
    
    for vac in vacancies:
        try:
            # ИСПОЛЬЗУЕМ ТОЛЬКО clean_text_safe для всех полей
            clean_vac = (
                vac['hh_id'],
                parser.clean_text_safe(vac['name'])[:500],
                parser.clean_text_safe(vac['company'])[:255], 
                vac['salary_from'], 
                vac['salary_to'], 
                vac['url'][:500],
                parser.clean_text_safe(vac['skills'])[:1000],
                parser.clean_text_safe(vac['description'])[:3000],
                parser.clean_text_safe(vac['category'])[:50],
                vac['relevance_score'], 
                parser.clean_text_safe(vac['work_format'])[:20], 
                parser.clean_text_safe(vac['city'])[:100]
            )
            
            cursor.execute("""
                INSERT INTO vacancies 
                (hh_id, name, company, salary_from, salary_to, url, skills, 
                 description, category, relevance_score, work_format, city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hh_id) DO NOTHING
                RETURNING id
            """, clean_vac)
            
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
    print(f"🕒 {datetime.now()} - Запуск ОПТИМИЗИРОВАННОГО парсера HH.ru")
    print(f"📍 Гео-фильтр: Тюмень - любой формат, другие города - только удаленка")
    print(f"💼 Опыт: без опыта или 1-3 года")
    print("=" * 60)
    
    parser = HHParser()
    vacancies = parser.get_hh_vacancies()
    
    print(f"\n🎯 Найдено подходящих вакансий: {len(vacancies)}")
    
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
