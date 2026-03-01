# update_data.py
from app import app
from models import db, Vacancy, Course, Skill
from scraper import JobScraper, CourseScraper
from datetime import datetime
import time
import argparse
import os
import sys


def save_vacancies_to_db(vacancies):
    """Сохранение вакансий в БД с проверкой дубликатов"""
    saved = 0
    skipped = 0

    for vac in vacancies:
        try:
            # Проверяем дубликаты по URL
            existing = Vacancy.query.filter_by(url=vac.get('url', '')).first()
            if not existing and vac.get('title'):
                vacancy = Vacancy(
                    title=vac['title'][:200],
                    company=vac.get('company', 'Не указано')[:100],
                    description=vac.get('description', '')[:1000],
                    requirements=vac.get('requirements', '')[:1000],
                    salary_min=vac.get('salary_min'),
                    salary_max=vac.get('salary_max'),
                    salary_currency=vac.get('salary_currency', 'RUB'),
                    location=vac.get('location', 'Не указано')[:100],
                    employment_type=vac.get('employment_type', 'full-time'),
                    url=vac.get('url', '#')[:500],
                    source=vac.get('source', 'unknown'),
                    posted_date=vac.get('posted_date', datetime.now())
                )
                db.session.add(vacancy)
                saved += 1

                # Добавляем навыки
                add_skills_from_title(vacancy, vac['title'])
                if vac.get('skills_list'):
                    for skill_name in vac['skills_list']:
                        add_skill_by_name(vacancy, skill_name)
            else:
                skipped += 1
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            continue

    if saved > 0:
        db.session.commit()
        print(f"   Сохранено: {saved}, пропущено: {skipped}")

    return saved


def save_courses_to_db(courses):
    """Сохранение курсов в БД"""
    saved = 0
    skipped = 0

    for course_data in courses:
        try:
            existing = Course.query.filter_by(url=course_data.get('url', '')).first()
            if not existing and course_data.get('title'):
                course = Course(
                    title=course_data['title'][:200],
                    provider=course_data.get('provider', 'Unknown')[:100],
                    description=course_data.get('description', '')[:1000],
                    level=course_data.get('level', 'intermediate'),
                    price=course_data.get('price', 0),
                    price_currency=course_data.get('price_currency', 'RUB'),
                    url=course_data.get('url', '#')[:500],
                    source=course_data.get('source', 'unknown'),
                    students_count=course_data.get('students_count', 0),
                    rating=course_data.get('rating', 4.5)
                )
                db.session.add(course)
                saved += 1

                # Добавляем навыки
                add_skills_from_title(course, course_data['title'])
            else:
                skipped += 1
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            continue

    if saved > 0:
        db.session.commit()
        print(f"   Сохранено: {saved}, пропущено: {skipped}")

    return saved


def add_skills_from_title(item, title):
    """Добавление навыков на основе названия"""
    title_lower = title.lower()

    all_skills = {
        'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript', 'js': 'JavaScript',
        'react': 'React', 'angular': 'Angular', 'vue': 'Vue.js', 'django': 'Django',
        'flask': 'Flask', 'sql': 'SQL', 'mysql': 'SQL', 'postgresql': 'SQL',
        'mongodb': 'MongoDB', 'docker': 'Docker', 'kubernetes': 'Kubernetes',
        'aws': 'AWS', 'azure': 'Azure', 'git': 'Git', 'linux': 'Linux',
        'devops': 'DevOps', 'machine learning': 'Machine Learning', 'ml': 'Machine Learning',
        'data science': 'Data Science', 'аналитик': 'Data Analysis', 'анализа': 'Data Analysis',
        'frontend': 'Frontend', 'backend': 'Backend', 'fullstack': 'Fullstack',
        'ios': 'iOS', 'android': 'Android', 'swift': 'Swift', 'kotlin': 'Kotlin',
        'c++': 'C++', 'c#': 'C#', 'php': 'PHP', 'ruby': 'Ruby', 'go': 'Golang',
        '1с': '1C', 'битрикс': 'Bitrix', 'wordpress': 'WordPress',
        'html': 'HTML', 'css': 'CSS', 'typescript': 'TypeScript',
        'node': 'Node.js', 'express': 'Express.js', 'spring': 'Spring',
        'tensorflow': 'TensorFlow', 'pandas': 'Pandas', 'scikit': 'Scikit-learn',
        'врач': 'Медицина', 'медсестра': 'Медицина', 'фельдшер': 'Медицина', 'фармацевт': 'Фармация',
        'учитель': 'Педагогика', 'преподаватель': 'Педагогика', 'воспитатель': 'Педагогика',
        'бухгалтер': 'Бухгалтерия', 'экономист': 'Финансы', 'аудитор': 'Аудит',
        'продавец': 'Продажи', 'кассир': 'Продажи', 'торговый представитель': 'Продажи',
        'строитель': 'Строительство', 'инженер': 'Инженерия', 'прораб': 'Строительство',
        'водитель': 'Вождение', 'логист': 'Логистика', 'экспедитор': 'Логистика', 'курьер': 'Доставка',
        'официант': 'Обслуживание', 'повар': 'Обслуживание', 'администратор': 'Администрирование',
        'директор': 'Управление', 'руководитель': 'Управление', 'начальник': 'Управление',
        'маркетолог': 'Маркетинг', 'реклама': 'Маркетинг', 'pr': 'Маркетинг', 'smm': 'Маркетинг',
        'hr': 'HR', 'кадровик': 'HR', 'рекрутер': 'HR',
        'дизайнер': 'Дизайн', 'художник': 'Дизайн', 'оформитель': 'Дизайн', 'верстальщик': 'Веб-дизайн',
        'юрист': 'Право', 'адвокат': 'Право', 'нотариус': 'Право', 'юрисконсульт': 'Право',
        'рабочий': 'Производство', 'оператор': 'Производство', 'станочник': 'Производство',
        'слесарь': 'Производство', 'агроном': 'Сельское хозяйство', 'ветеринар': 'Ветеринария',
        'тракторист': 'Сельское хозяйство', 'фермер': 'Сельское хозяйство'
    }

    for tech, skill_name in all_skills.items():
        if tech in title_lower:
            add_skill_by_name(item, skill_name)


def add_skill_by_name(item, skill_name):
    """Добавление конкретного навыка к элементу"""
    skill = Skill.query.filter_by(name=skill_name).first()
    if skill and skill not in item.skills:
        item.skills.append(skill)


def update_vacancies(scraper, quick=False, categories=None):
    """Обновление только вакансий"""
    print("\n" + "=" * 60)
    print("📊 ОБНОВЛЕНИЕ ВАКАНСИЙ")
    print("=" * 60)

    if quick:
        search_queries = ["Python", "Java", "JavaScript", "Frontend", "Backend", "DevOps", "QA", "Data Science"]
    else:
        search_queries = [
            "программист", "разработчик", "системный администратор", "тестировщик",
            "врач", "медсестра", "фельдшер", "фармацевт",
            "учитель", "преподаватель", "воспитатель", "педагог",
            "бухгалтер", "экономист", "финансист", "аудитор",
            "продавец", "менеджер по продажам", "кассир", "торговый представитель",
            "строитель", "инженер", "прораб", "отделочник",
            "водитель", "логист", "экспедитор", "курьер",
            "официант", "повар", "администратор", "уборщица",
            "директор", "руководитель", "начальник", "менеджер",
            "маркетолог", "реклама", "pr", "smm",
            "hr", "кадровик", "рекрутер", "специалист по персоналу",
            "дизайнер", "художник", "оформитель", "верстальщик",
            "юрист", "адвокат", "нотариус", "юрисконсульт",
            "рабочий", "оператор", "станочник", "слесарь",
            "агроном", "ветеринар", "тракторист", "фермер"
        ]

    # Фильтрация по категориям
    if categories:
        filtered_queries = []
        category_keywords = {
            'it': ['программист', 'разработчик', 'администратор', 'тестировщик', 'Python', 'Java', 'JavaScript'],
            'medicine': ['врач', 'медсестра', 'фельдшер', 'фармацевт'],
            'education': ['учитель', 'преподаватель', 'воспитатель', 'педагог'],
            'finance': ['бухгалтер', 'экономист', 'финансист', 'аудитор'],
            'sales': ['продавец', 'менеджер по продажам', 'кассир', 'торговый представитель'],
            'construction': ['строитель', 'инженер', 'прораб', 'отделочник'],
            'transport': ['водитель', 'логист', 'экспедитор', 'курьер'],
            'service': ['официант', 'повар', 'администратор', 'уборщица'],
            'management': ['директор', 'руководитель', 'начальник', 'менеджер'],
            'marketing': ['маркетолог', 'реклама', 'pr', 'smm'],
            'hr': ['hr', 'кадровик', 'рекрутер', 'специалист по персоналу'],
            'design': ['дизайнер', 'художник', 'оформитель', 'верстальщик'],
            'law': ['юрист', 'адвокат', 'нотариус', 'юрисконсульт'],
            'manufacturing': ['рабочий', 'оператор', 'станочник', 'слесарь'],
            'agriculture': ['агроном', 'ветеринар', 'тракторист', 'фермер']
        }

        for query in search_queries:
            for category in categories:
                if category in category_keywords:
                    if any(keyword in query.lower() for keyword in category_keywords[category]):
                        filtered_queries.append(query)
                        break
        search_queries = filtered_queries

    if not search_queries:
        print("❌ Нет запросов для выбранных категорий")
        return 0

    all_vacancies = []
    total_queries = len(search_queries)

    for idx, query in enumerate(search_queries, 1):
        print(f"\n🔍 Поиск вакансий {idx}/{total_queries}: '{query}'")
        vacancies = scraper.parse_all_sources(query, pages=1)
        all_vacancies.extend(vacancies)
        print(f"   Собрано: {len(vacancies)} вакансий")
        time.sleep(2)

    if all_vacancies:
        saved = save_vacancies_to_db(all_vacancies)
        print(f"\n✅ Сохранено вакансий: {saved}")
        return saved
    return 0


def update_courses(scraper, quick=False, categories=None):
    """Обновление только курсов"""
    print("\n" + "=" * 60)
    print("📚 ОБНОВЛЕНИЕ КУРСОВ")
    print("=" * 60)

    if quick:
        course_queries = ["программирование", "медицина", "педагогика", "финансы", "маркетинг", "дизайн"]
    else:
        course_queries = [
            "программирование", "медицина", "педагогика", "финансы",
            "маркетинг", "дизайн", "иностранный язык", "психология",
            "бухгалтерия", "управление", "строительство", "электроника"
        ]

    # Фильтрация по категориям
    if categories:
        filtered_queries = []
        category_keywords = {
            'programming': ['программирование', 'python', 'java', 'javascript'],
            'medicine': ['медицина', 'здоровье'],
            'education': ['педагогика', 'образование'],
            'finance': ['финансы', 'бухгалтерия', 'экономика'],
            'marketing': ['маркетинг', 'реклама'],
            'design': ['дизайн', 'графика'],
            'languages': ['иностранный язык', 'английский', 'немецкий'],
            'psychology': ['психология'],
            'management': ['управление', 'менеджмент'],
            'construction': ['строительство'],
            'engineering': ['электроника', 'инженерия'],
            'business': ['бизнес', 'предпринимательство']
        }

        for query in course_queries:
            for category in categories:
                if category in category_keywords:
                    if any(keyword in query.lower() for keyword in category_keywords[category]):
                        filtered_queries.append(query)
                        break
        course_queries = filtered_queries

    if not course_queries:
        print("❌ Нет запросов для выбранных категорий")
        return 0

    all_courses = []
    total_queries = len(course_queries)

    for idx, query in enumerate(course_queries, 1):
        print(f"\n🔍 Поиск курсов {idx}/{total_queries}: '{query}'")
        courses = scraper.parse_all_sources(query, pages=1)
        all_courses.extend(courses)
        print(f"   Собрано: {len(courses)} курсов")
        time.sleep(2)

    if all_courses:
        saved = save_courses_to_db(all_courses)
        print(f"\n✅ Сохранено курсов: {saved}")
        return saved
    return 0


def update_data(quick=False, categories=None, vacancies_only=False, courses_only=False):
    """Обновление данных парсингом"""
    with app.app_context():
        print("=" * 60)
        print("🔄 ОБНОВЛЕНИЕ ДАННЫХ ПАРСИНГОМ")
        print("=" * 60)

        # Создаем экземпляры парсеров
        job_scraper = JobScraper()
        course_scraper = CourseScraper()

        # Обновление вакансий
        if not courses_only:
            update_vacancies(job_scraper, quick, categories)

        # Обновление курсов
        if not vacancies_only:
            update_courses(course_scraper, quick, categories)

        # Сохраняем время последнего обновления
        try:
            with open('last_update.txt', 'w') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except:
            pass

        # Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА ПОСЛЕ ОБНОВЛЕНИЯ:")
        print("=" * 60)
        print(f"📊 Вакансий: {Vacancy.query.count()}")
        print(f"📚 Курсов: {Course.query.count()}")
        print(f"🏷️  Навыков: {Skill.query.count()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обновление данных парсингом')
    parser.add_argument('--quick', action='store_true', help='Быстрое обновление (только IT)')
    parser.add_argument('--categories', nargs='+', help='Категории для обновления')
    parser.add_argument('--vacancies-only', action='store_true', help='Обновлять только вакансии')
    parser.add_argument('--courses-only', action='store_true', help='Обновлять только курсы')

    args = parser.parse_args()
    update_data(
        quick=args.quick,
        categories=args.categories,
        vacancies_only=args.vacancies_only,
        courses_only=args.courses_only
    )