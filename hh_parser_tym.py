import requests
import psycopg2
import time
import re
import html
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'hh_parser'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432')
}

class TyumenOfficeITJobs:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH-Tyumen-Office-IT/1.0',
            'Accept': 'application/json'
        })
    
    def clean_text_safe(self, text, max_length=2000):
        if not text:
            return ""
        try:
            text = html.unescape(text)
            cleaned = re.sub(r'[^\w\s\.\,\-\+\!\?\:\;\(\)\"\'\/\\\@\#\$\&\*\=\[\]\{\}\<\>\|\~\`\n\rа-яА-ЯёЁ]', ' ', text, flags=re.UNICODE)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()[:max_length]
        except Exception:
            return ""
    
    def clean_html_tags(self, text):
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_tyumen_vacancies_strict(self):
        """СТРОГИЙ поиск: офисные + IT/технические вакансии"""
        url = "https://api.hh.ru/vacancies"
        all_vacancies = []
        
        # Раздельные запросы для разных категорий
        search_queries = {
            'office': (
                '"офис-менеджер" OR "помощник руководителя" OR "помощник директора" OR '
                '"делопроизводитель" OR "архивариус" OR "документовед" OR '
                '"канцелярия" OR "офисный работник" OR "ресепшионист" OR '
                '"оператор данных" OR "ввод данных" OR "обработка документов" OR '
                '"регистратор документов" OR "секретарь-делопроизводитель"'
            ),
            'it_tech': (
                '"системный аналитик" OR "бизнес-аналитик" OR "data analyst" OR '
                '"аналитик данных" OR "sql" OR "базы данных" OR '
                '"1с разработчик" OR "1с программист" OR "программист 1с" OR '
                '"тестировщик" OR "qa engineer" OR "qa специалист" OR '
                '"junior разработчик" OR "младший программист" OR "стажер программист" OR '
                '"стажер it" OR "junior it" OR "начальный уровень программист"'
            )
        }
        
        for category_type, search_query in search_queries.items():
            print(f"\n🔍 Поиск {category_type.upper()} вакансий Тюмени...")
            print(f"📝 Запрос: {search_query[:80]}...")
            
            params = {
                'text': search_query,
                'area': 95,  # Тюмень
                'per_page': 100,
                'page': 0,
                'period': 30,
            }
            
            try:
                response = self.session.get(url, params=params, timeout=15)
                data = response.json()
                
                found = data.get('found', 0)
                pages = min(data.get('pages', 1), 5)
                
                print(f"📨 Найдено по запросу: {found}")
                
                for page in range(pages):
                    if page > 0:
                        params['page'] = page
                        response = self.session.get(url, params=params, timeout=15)
                        data = response.json()
                    
                    for item in data.get('items', []):
                        try:
                            vacancy_id = item['id']
                            name = item.get('name', '').lower()
                            city = item.get('area', {}).get('name', 'Не указан')
                            
                            # ФИЛЬТР 1: ТОЛЬКО Тюмень
                            if not ('тюмен' in city.lower()):
                                continue
                            
                            # ФИЛЬТР 2: КОНТЕКСТНЫЕ ИСКЛЮЧЕНИЯ
                            # Общие исключения для ВСЕХ категорий
                            context_exclude = [
                                # Продажи и торговля
                                'продаж', 'менеджер по продажам', 'продавец', 'торговый',
                                'консультант по продажам', 'мерчендайзер', 'кассир',
                                'товаровед', 'закупк', 'снабжен',
                                
                                # Клиентский сервис и звонки
                                'оператор call', 'оператор колл', 'диспетчер',
                                'телефонный оператор', 'прием звонков', 'звонк',
                                'call-центр', 'колл-центр', 'клиентский сервис',
                                'обслуживание клиентов', 'консультирование',
                                
                                # Управление и высокие позиции
                                'руководитель', 'директор', 'начальник', 'управляющий',
                                'заместитель директора', 'зам. директора', 'генеральный',
                                'ведущий', 'старший', 'senior', 'team lead', 'руковод',
                                
                                # Неподходящие профессии
                                'водитель', 'курьер', 'экспедитор', 'грузчик',
                                'упаковщик', 'кладовщик', 'комплектовщик',
                                'охрана', 'охранник', 'консьерж',
                                'повар', 'официант', 'бармен', 'промоутер',
                                'мастер', 'техник', 'механик', 'электрик',
                                'монтажник', 'сварщик', 'слесарь',
                                'медсестра', 'медбрат', 'врач', 'фельдшер',
                                'воспитатель', 'учитель', 'преподаватель',
                                'уборщик', 'уборщица', 'клининг', 'дворник',
                                'парикмахер', 'визажист', 'массажист', 'косметолог',
                                
                                # Маркетинг и SMM
                                'маркетолог', 'smm', 'таргетолог', 'копирайтер',
                                'контент-менеджер', 'дизайнер', 'иллюстратор',
                                
                                # HR и рекрутинг
                                'hr', 'рекрутер', 'менеджер по персоналу',
                                
                                # Логистика
                                'логист', 'диспетчер грузоперевозок',
                                
                                # Инженеры (не IT)
                                'инженер', 'проектировщик', 'конструктор', 'технолог',
                                
                                # Сфера услуг (сауны, фитнес и т.д.)
                                'саун', 'спа', 'фитнес', 'тренажер', 'зал',
                                'бассейн', 'косметолог', 'массаж', 'салон',
                                'гостиниц', 'отель', 'ресторан', 'кафе', 'бар',
                                'клуб', 'развлекательный центр',
                                
                                # Авто и транспорт
                                'авто', 'автомобил', 'шиномонтаж', 'автомойк',
                                'автосервис', 'стоянк', 'парковк',
                                
                                # Производство и склад
                                'склад', 'производств', 'цех', 'завод',
                                'фабрик', 'оборудован', 'механизм',
                                
                                # Слишком высокий уровень
                                'архитектор', 'devops', 'sre', 'security',
                                'сетевой инженер', 'системный администратор',
                                'главный', 'ведущий', 'principal', 'architect'
                            ]
                            
                            excluded = False
                            for excl in context_exclude:
                                if excl in name:
                                    excluded = True
                                    break
                            
                            if excluded:
                                continue
                            
                            # Дополнительные проверки для "Администратор"
                            if 'администратор' in name:
                                admin_context_exclude = [
                                    'саун', 'спа', 'клуб', 'кафе', 'ресторан', 'бар',
                                    'гостиниц', 'отель', 'фитнес', 'тренажер', 'зал',
                                    'клиник', 'больниц', 'стоматолог', 'поликлиник',
                                    'авто', 'автомойк', 'стоянк', 'парковк',
                                    'склад', 'производств', 'цех', 'завод',
                                    'магазин', 'торгов', 'школ', 'детск', 'садик'
                                ]
                                
                                if any(ctx in name for ctx in admin_context_exclude):
                                    continue
                            
                            # ФИЛЬТР 3: Получаем сниппет для проверки
                            snippet = item.get('snippet', {})
                            requirement = snippet.get('requirement', '').lower()
                            responsibility = snippet.get('responsibility', '').lower()
                            snippet_text = f"{requirement} {responsibility}"
                            
                            # ФИЛЬТР 4: Проверяем что это подходящая категория
                            category = self.categorize_vacancy(name, snippet_text, category_type)
                            
                            if category == 'excluded':
                                continue
                            
                            # ФИЛЬТР 5: Опыт (только для начинающих/младших)
                            experience_id = item.get('experience', {}).get('id', '')
                            
                            # Для IT: разрешаем до 6 лет, но проверяем уровень
                            allowed_experience = ['noExperience', 'between1And3', 'between3And6']
                            
                            if experience_id not in allowed_experience:
                                continue
                            
                            # Для опытных IT проверяем что не senior/lead
                            if experience_id == 'between3And6' or experience_id == 'moreThan6':
                                if any(level in name for level in ['senior', 'ведущий', 'старший', 'lead', 'руководитель']):
                                    continue
                            
                            # ФИЛЬТР 6: Получаем полное описание для IT
                            if category in ['it_analyst', 'it_developer', 'it_1c', 'it_tester']:
                                try:
                                    detail_response = self.session.get(
                                        f"https://api.hh.ru/vacancies/{vacancy_id}",
                                        timeout=3
                                    )
                                    if detail_response.status_code == 200:
                                        vacancy_detail = detail_response.json()
                                        full_description = vacancy_detail.get('description', '').lower()
                                        
                                        # Для IT: проверяем что не высокие требования
                                        it_exclude_terms = [
                                            'senior', 'lead', 'team lead', 'архитектор',
                                            'руководитель', 'управление командой',
                                            '5+ лет', '6+ лет', '7+ лет', 'более 5 лет',
                                            'опыт от 5 лет', 'опыт от 6 лет'
                                        ]
                                        
                                        if any(term in full_description for term in it_exclude_terms):
                                            continue
                                        
                                        description_text = full_description
                                    else:
                                        description_text = snippet_text
                                except:
                                    description_text = snippet_text
                            else:
                                description_text = snippet_text
                            
                            # ВСЕ ФИЛЬТРЫ ПРОЙДЕНЫ - обрабатываем
                            
                            # Зарплата
                            salary_data = item.get('salary')
                            salary_from = None
                            salary_to = None
                            
                            if salary_data:
                                salary_from = salary_data.get('from')
                                salary_to = salary_data.get('to')
                                
                                if salary_data.get('currency') != 'RUR':
                                    rate = 90 if salary_data.get('currency') == 'USD' else 100 if salary_data.get('currency') == 'EUR' else 1
                                    if salary_from:
                                        salary_from = int(salary_from * rate)
                                    if salary_to:
                                        salary_to = int(salary_to * rate)
                            
                            # Формат работы
                            schedule = item.get('schedule', {})
                            schedule_id = schedule.get('id', '')
                            
                            if schedule_id == 'remote':
                                work_format = 'remote'
                            elif schedule_id == 'flexible':
                                work_format = 'hybrid'
                            else:
                                work_format = 'office'
                            
                            # Уточняем по названию
                            if 'удален' in name or 'remote' in name:
                                work_format = 'remote'
                            elif 'гибрид' in name or 'hybrid' in name:
                                work_format = 'hybrid'
                            
                            # Навыки
                            skills_list = item.get('key_skills', [])
                            skills = ', '.join([skill['name'] for skill in skills_list])
                            
                            # Описание
                            cleaned_description = self.clean_html_tags(description_text)
                            cleaned_description = self.clean_text_safe(cleaned_description)[:2000]
                            
                            # Релевантность
                            relevance_score = self.calculate_relevance(name, description_text, 
                                                                      experience_id, work_format, 
                                                                      salary_from, category)
                            
                            # Формируем вакансию
                            vacancy = {
                                'hh_id': int(vacancy_id),
                                'name': self.clean_text_safe(item.get('name', '')),
                                'company': self.clean_text_safe(item.get('employer', {}).get('name', '')),
                                'salary_from': salary_from,
                                'salary_to': salary_to,
                                'url': item.get('alternate_url', f'https://hh.ru/vacancy/{vacancy_id}'),
                                'skills': self.clean_text_safe(skills)[:500],
                                'description': cleaned_description,
                                'work_format': work_format,
                                'city': city,
                                'category': category,
                                'relevance_score': relevance_score
                            }
                            
                            # Проверяем дубликаты
                            if not any(v['hh_id'] == vacancy['hh_id'] for v in all_vacancies):
                                all_vacancies.append(vacancy)
                                
                                salary_display = ""
                                if salary_from or salary_to:
                                    salary_display = f" ({salary_from or '?'}-{salary_to or '?'} руб)"
                                
                                exp_display = ""
                                if experience_id == 'noExperience':
                                    exp_display = " | без опыта"
                                elif experience_id == 'between1And3':
                                    exp_display = " | 1-3 года"
                                
                                print(f"✅ {category}: {vacancy['name'][:50]}{exp_display}{salary_display}")
                            
                        except Exception as e:
                            continue
                    
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️ Ошибка запроса: {e}")
                continue
        
        print(f"\n🎯 ИТОГО найдено подходящих вакансий: {len(all_vacancies)}")
        return all_vacancies
    
    def categorize_vacancy(self, name, snippet_text, search_type):
        """Категоризация с проверкой соответствия"""
        text = f"{name} {snippet_text}"
        
        # IT/Технические категории (строго по ключевым словам)
        if 'аналитик' in name and ('системн' in text or 'бизнес' in text or 'данн' in text):
            return 'it_analyst'
        
        if 'sql' in text or 'баз данн' in text or 'data analyst' in text:
            if 'аналитик' in name or 'специалист' in name:
                return 'it_analyst'
        
        if '1с' in name or '1c' in name:
            if any(kw in text for kw in ['программист', 'разработчик', 'специалист']):
                return 'it_1c'
        
        if any(kw in name for kw in ['тестировщик', 'qa', 'quality assurance']):
            return 'it_tester'
        
        if any(kw in name for kw in ['junior разработчик', 'младший программист', 
                                     'стажер программист', 'программист стажер']):
            if not any(kw in name for kw in ['senior', 'ведущий', 'старший']):
                return 'it_developer'
        
        # Офисные категории
        if search_type == 'office':
            if 'офис-менеджер' in name or 'офисный' in name:
                return 'office_manager'
            
            if any(kw in name for kw in ['помощник руководителя', 'помощник директора', 
                                        'ассистент руководителя']):
                return 'assistant'
            
            if 'делопроизводитель' in name or 'канцелярия' in name:
                return 'clerk'
            
            if 'архивариус' in name or 'архив' in name:
                return 'archivist'
            
            if 'документовед' in name or 'документ' in name:
                return 'document_specialist'
            
            if 'ресепшионист' in name or 'приемная' in name:
                return 'receptionist'
            
            if any(kw in name for kw in ['оператор данн', 'ввод данн', 'обработк данн']):
                return 'data_operator'
        
        return 'excluded'  # Не подходит ни под одну категорию
    
    def calculate_relevance(self, name, description, experience_id, work_format, salary_from, category):
        """Расчет релевантности"""
        score = 5
        text = f"{name} {description}"
        
        # Опыт
        if experience_id == 'noExperience':
            score += 3
        elif experience_id == 'between1And3':
            score += 2
        elif experience_id == 'between3And6':
            score += 1
        
        # Формат работы
        if work_format == 'remote':
            score += 2
        elif work_format == 'hybrid':
            score += 1
        
        # Зарплата (оптимальный диапазон)
        if salary_from:
            if 30000 <= salary_from <= 60000:  # Для начинающих
                score += 2
            elif salary_from > 60000:  # Высокая ЗП - может быть сложно
                score -= 1
        
        # Ключевые слова для начинающих
        if any(kw in text for kw in ['без опыта', 'начинающий', 'стажер', 'студент', 'обучение']):
            score += 2
        
        # Для IT: бонус за конкретные технологии
        if category in ['it_analyst', 'it_developer', 'it_1c', 'it_tester']:
            if any(tech in text for tech in ['python', 'sql', '1с', 'excel', 'tableau']):
                score += 1
        
        return min(max(score, 1), 10)  # Ограничиваем 1-10

def save_to_db_strict(vacancies):
    """Сохранение в БД"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    error_count = 0
    
    parser = TyumenOfficeITJobs()
    
    for vac in vacancies:
        try:
            clean_data = (
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
                vac['work_format'][:20],
                parser.clean_text_safe(vac['city'])[:100]
            )
            
            cursor.execute("""
                INSERT INTO vacancies 
                (hh_id, name, company, salary_from, salary_to, url, skills, 
                 description, category, relevance_score, work_format, city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hh_id) DO NOTHING
                RETURNING id
            """, clean_data)
            
            if cursor.fetchone():
                new_count += 1
            else:
                duplicate_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"❌ Ошибка сохранения вакансии {vac['hh_id']}: {e}")
    
    conn.commit()
    
    # Статистика
    cursor.execute("SELECT COUNT(*) FROM vacancies WHERE city LIKE '%Тюмен%'")
    total_tyumen = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT category, COUNT(*) 
        FROM vacancies 
        WHERE city LIKE '%Тюмен%' 
        GROUP BY category 
        ORDER BY COUNT(*) DESC
    """)
    categories_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return new_count, duplicate_count, error_count, total_tyumen, categories_stats

if __name__ == "__main__":
    print(f"🕒 {datetime.now()} - Парсер Тюмень (офисные + IT)")
    print("📍 Город: Тюмень")
    print("🎯 Категории: офисные, административные, IT/технические (только начинающие)")
    print("🚫 ИСКЛЮЧЕНО: продажи, звонки, управление, сфера услуг, высокие позиции")
    print("💼 Уровень: без опыта, junior, младший специалист")
    print("=" * 70)
    
    parser = TyumenOfficeITJobs()
    vacancies = parser.get_tyumen_vacancies_strict()
    
    print(f"\n📊 Найдено подходящих вакансий: {len(vacancies)}")
    
    if vacancies:
        new_count, duplicate_count, error_count, total_tyumen, categories_stats = save_to_db_strict(vacancies)
        
        print(f"\n💾 Результаты сохранения:")
        print(f"  Новых: {new_count}")
        print(f"  Дубликатов: {duplicate_count}")
        print(f"  Ошибок: {error_count}")
        print(f"  Всего по Тюмени в БД: {total_tyumen}")
        
        # Статистика из найденных
        categories_found = {}
        formats_found = {}
        
        for vac in vacancies:
            cat = vac['category']
            fmt = vac['work_format']
            
            categories_found[cat] = categories_found.get(cat, 0) + 1
            formats_found[fmt] = formats_found.get(fmt, 0) + 1
        
        print(f"\n📊 Категории найденных:")
        for cat, count in sorted(categories_found.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")
        
        print(f"\n📊 Форматы работы:")
        for fmt, count in formats_found.items():
            print(f"  {fmt}: {count}")
        
        # Топ по релевантности
        print(f"\n🏆 Топ-10 по релевантности:")
        sorted_vacancies = sorted(vacancies, key=lambda x: x['relevance_score'], reverse=True)[:10]
        for i, vac in enumerate(sorted_vacancies, 1):
            salary = ""
            if vac['salary_from'] or vac['salary_to']:
                salary = f" ({vac['salary_from'] or '?'}-{vac['salary_to'] or '?'} руб)"
            print(f"  {i}. [{vac['relevance_score']}/10] {vac['category']}: {vac['name'][:55]}{salary}")
            
    else:
        print("❌ Подходящих вакансий не найдено")