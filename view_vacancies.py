import psycopg2
import webbrowser
from datetime import datetime, timedelta
from config import DB_CONFIG

def format_salary(salary_from, salary_to):
    """Форматирование зарплаты для отображения"""
    if salary_from and salary_to:
        return f"{salary_from:,} - {salary_to:,} руб."
    elif salary_from:
        return f"от {salary_from:,} руб."
    elif salary_to:
        return f"до {salary_to:,} руб."
    else:
        return "не указана"

def format_work_format(work_format, city):
    """Форматирование информации о формате работы"""
    format_icons = {
        'remote': '🏠',
        'hybrid': '⚡', 
        'office': '🏢',
        'unknown': '❓'
    }
    
    icon = format_icons.get(work_format, '❓')
    return f"{icon} {work_format} | 📍 {city}"

def show_vacancies():
    """Интерактивный просмотр вакансий с гео-фильтрацией"""
    print("🎯 УНИВЕРСАЛЬНЫЙ ПАРСЕР ВАКАНСИЙ HH.RU")
    print("📍 ФИЛЬТРАЦИЯ: Тюмень - любой формат, другие города - только удаленка/гибрид")
    print("=" * 70)
    
    # Настройка фильтров
    try:
        days = int(input("За сколько дней показать вакансии? (1-30): ") or "7")
        days = max(1, min(30, days))
    except:
        days = 7
    
    print("\n📂 Категории: automation, data_engineering, bi, python_sql, excel, all")
    category = input("Выберите категорию (Enter = все): ").strip().lower() or "all"
    
    print("\n💼 Формат работы: remote, hybrid, office, all")
    work_format_filter = input("Формат работы (Enter = все): ").strip().lower() or "all"
    
    try:
        min_salary = int(input("Мин. зарплата (Enter = любая): ") or "0")
    except:
        min_salary = 0
    
    # Получение данных из БД
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    query = """
        SELECT name, company, salary_from, salary_to, url, category, 
               skills, created_date, relevance_score, hh_id, work_format, city
        FROM vacancies 
        WHERE created_date >= %s
    """
    params = [datetime.now() - timedelta(days=days)]
    
    if category != 'all':
        query += " AND category = %s"
        params.append(category)
    
    if work_format_filter != 'all':
        query += " AND work_format = %s"
        params.append(work_format_filter)
    
    if min_salary > 0:
        query += " AND (salary_from >= %s OR salary_to >= %s)"
        params.extend([min_salary, min_salary])
    
    query += " ORDER BY relevance_score DESC, created_date DESC"
    
    cursor.execute(query, params)
    vacancies = cursor.fetchall()
    
    print(f"\n📊 Найдено вакансий: {len(vacancies)}")
    print("=" * 90)
    
    if not vacancies:
        print("❌ Вакансии не найдены по заданным критериям")
        return
    
    # Отображение вакансий
    for i, vac in enumerate(vacancies, 1):
        name, company, salary_from, salary_to, url, category, skills, created, score, hh_id, work_format, city = vac
        
        salary_str = format_salary(salary_from, salary_to)
        location_str = format_work_format(work_format, city)
        
        print(f"{i}. {name}")
        print(f"   🏢 {company} | 🏷️ {category} | ⭐ {score}/10")
        print(f"   💵 {salary_str}")
        print(f"   {location_str}")
        
        if skills:
            print(f"   🛠️  {skills[:100]}{'...' if len(skills) > 100 else ''}")
        
        print(f"   🔗 {url}")
        print(f"   📅 {created.strftime('%d.%m.%Y %H:%M')}")
        print("-" * 90)
    
    # Интерактивный выбор для открытия ссылки
    while True:
        try:
            choice = input("\nВведите номер вакансии для открытия (0 для выхода): ").strip()
            
            if choice == '0':
                break
            
            vacancy_num = int(choice)
            if 1 <= vacancy_num <= len(vacancies):
                selected_vacancy = vacancies[vacancy_num - 1]
                url = selected_vacancy[4]  # URL находится на 5-й позиции
                
                print(f"Открываю: {selected_vacancy[0]}")
                webbrowser.open(url)
            else:
                print("❌ Неверный номер вакансии")
                
        except ValueError:
            print("❌ Введите корректный номер")
        except Exception as e:
            print(f"❌ Ошибка при открытии ссылки: {e}")
    
    cursor.close()
    conn.close()

def show_statistics():
    """Показать статистику по вакансиям с гео-информацией"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Статистика по категориям
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as count,
            AVG(COALESCE(salary_from, salary_to)) as avg_salary
        FROM vacancies 
        WHERE created_date >= NOW() - INTERVAL '7 days'
        GROUP BY category
        ORDER BY count DESC
    """)
    
    stats = cursor.fetchall()
    
    # Статистика по форматам работы
    cursor.execute("""
        SELECT 
            work_format,
            COUNT(*) as count
        FROM vacancies 
        WHERE created_date >= NOW() - INTERVAL '7 days'
        GROUP BY work_format
        ORDER BY count DESC
    """)
    
    format_stats = cursor.fetchall()
    
    # Статистика по городам
    cursor.execute("""
        SELECT 
            city,
            COUNT(*) as count
        FROM vacancies 
        WHERE created_date >= NOW() - INTERVAL '7 days'
        GROUP BY city
        ORDER BY count DESC
        LIMIT 10
    """)
    
    city_stats = cursor.fetchall()
    
    print("\n📈 СТАТИСТИКА ЗА ПОСЛЕДНИЕ 7 ДНЕЙ:")
    print("=" * 50)
    
    total_vacancies = 0
    print("\n📂 По категориям:")
    for category, count, avg_salary in stats:
        total_vacancies += count
        salary_str = f"{int(avg_salary or 0):,} руб." if avg_salary else "не указана"
        print(f"  {category:15} | {count:3} вакансий | средняя: {salary_str}")
    
    print(f"\n💼 По форматам работы:")
    for work_format, count in format_stats:
        print(f"  {work_format:10} | {count:3} вакансий")
    
    print(f"\n📍 По городам (топ-10):")
    for city, count in city_stats:
        print(f"  {city:20} | {count:3} вакансий")
    
    print(f"\nВсего вакансий: {total_vacancies}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    while True:
        print("\n" + "="*50)
        print("🎯 СИСТЕМА МОНИТОРИНГА ВАКАНСИЙ")
        print("1 - Просмотр вакансий")
        print("2 - Статистика")
        print("3 - Выход")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            show_vacancies()
        elif choice == '2':
            show_statistics()
        elif choice == '3':
            print("До свидания!")
            break
        else:
            print("❌ Неверный выбор")