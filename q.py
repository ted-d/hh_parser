import requests
import re

def clean_html_tags(text):
    """Очистка текста от HTML тегов - с обработкой битых тегов"""
    if not text:
        return ""
    
    import re
    
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
def extract_skills_from_text(text):
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

def test_html_cleaning():
    """Тестируем улучшенную очистку HTML"""
    print("🎯 ТЕСТ УЛУЧШЕННОЙ ОЧИСТКИ HTML")
    print("=" * 50)
    
    test_cases = [
        "li>Разработка и поддержка сервисов</li> <li>Оптимизация</li>",
        "<p>О компании</p> <p>Мы разрабатываем финтех-платформы",
        "<strong>Задачи:</strong> <ul> <li>Разработка</li>",
        "li>Текст без закрывающего тега",
        "<br>Переносы строк<br>",
    ]
    
    for i, html in enumerate(test_cases, 1):
        cleaned = clean_html_tags(html)
        print(f"\n{i}. Исходный: {html}")
        print(f"   Очищенный: {cleaned}")

# Запускаем тест
if __name__ == "__main__":
    test_html_cleaning()