from models import db, User, Skill, Vacancy, Course, SearchHistory, ViewHistory
from datetime import datetime, timedelta
import json


class DatabaseManager:
    def __init__(self):
        self.db = db

    def create_user(self, username, email, password, **kwargs):
        """Создание нового пользователя"""
        try:
            user = User(username=username, email=email, **kwargs)
            user.set_password(password)
            self.db.session.add(user)
            self.db.session.commit()
            return user
        except Exception as e:
            print(f"Ошибка при создании пользователя: {e}")
            self.db.session.rollback()
            return None

    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        return User.query.get(user_id)

    def get_user_by_email(self, email):
        """Получение пользователя по email"""
        return User.query.filter_by(email=email).first()

    def add_skill(self, name, category=None):
        """Добавление нового навыка"""
        try:
            skill = Skill.query.filter_by(name=name).first()
            if not skill:
                skill = Skill(name=name, category=category)
                self.db.session.add(skill)
                self.db.session.commit()
            return skill
        except Exception as e:
            print(f"Ошибка при добавлении навыка: {e}")
            self.db.session.rollback()
            return None

    def get_all_skills(self):
        """Получение всех навыков"""
        return Skill.query.all()

    def add_user_skill(self, user_id, skill_id, level=1):
        """Добавление навыка пользователю"""
        try:
            user = self.get_user_by_id(user_id)
            skill = Skill.query.get(skill_id)
            if user and skill and skill not in user.skills:
                user.skills.append(skill)
                self.db.session.commit()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при добавлении навыка пользователю: {e}")
            self.db.session.rollback()
            return False

    def search_vacancies(self, query=None, skills=None, salary_min=None,
                         location=None, employment_type=None, page=1, per_page=20):
        """Поиск вакансий с фильтрацией"""
        try:
            # Начинаем с базового запроса
            vacancies_query = Vacancy.query

            # Фильтр по поисковому запросу
            if query and query.strip():
                search_term = f"%{query.strip()}%"
                vacancies_query = vacancies_query.filter(
                    (Vacancy.title.ilike(search_term)) |
                    (Vacancy.description.ilike(search_term)) |
                    (Vacancy.company.ilike(search_term))
                )
                print(f"Поиск по запросу: {query}")

            # Фильтр по навыкам - ИСПРАВЛЕНО
            if skills and len(skills) > 0 and skills[0]:
                print(f"Фильтр по навыкам: {skills}")
                # Для каждого навыка добавляем условие
                for skill_name in skills:
                    if skill_name and skill_name.strip():
                        # Проверяем существование навыка
                        skill = Skill.query.filter_by(name=skill_name).first()
                        if skill:
                            vacancies_query = vacancies_query.filter(
                                Vacancy.skills.any(id=skill.id)
                            )
                            print(f"   Фильтр по навыку ID {skill.id}: {skill_name}")
                        else:
                            print(f"   Навык не найден: {skill_name}")

            # Фильтр по минимальной зарплате
            if salary_min and salary_min > 0:
                print(f"Фильтр по зарплате от: {salary_min}")
                vacancies_query = vacancies_query.filter(
                    (Vacancy.salary_min >= salary_min) |
                    (Vacancy.salary_max >= salary_min)
                )

            # Фильтр по локации
            if location and location.strip():
                location_term = f"%{location.strip()}%"
                print(f"Фильтр по локации: {location}")
                vacancies_query = vacancies_query.filter(
                    Vacancy.location.ilike(location_term)
                )

            # Фильтр по типу занятости
            if employment_type and employment_type.strip():
                print(f"Фильтр по типу занятости: {employment_type}")
                vacancies_query = vacancies_query.filter(
                    Vacancy.employment_type == employment_type
                )

            # Сортировка по дате
            vacancies_query = vacancies_query.order_by(Vacancy.posted_date.desc())

            # Подсчет общего количества
            total = vacancies_query.count()
            print(f"Найдено вакансий до пагинации: {total}")

            # Пагинация
            result = vacancies_query.paginate(page=page, per_page=per_page, error_out=False)

            print(f"Результаты: страница {page}, показано {len(result.items)} из {result.total}")
            print(f"Всего страниц: {result.pages}")

            return result

        except Exception as e:
            print(f"Ошибка при поиске вакансий: {e}")
            import traceback
            traceback.print_exc()

            # Возвращаем пустой результат с правильной структурой
            class EmptyPagination:
                def __init__(self):
                    self.items = []
                    self.total = 0
                    self.pages = 0
                    self.page = page
                    self.per_page = per_page
                    self.has_prev = False
                    self.has_next = False
                    self.prev_num = None
                    self.next_num = None

                def iter_pages(self, left_edge=2, left_current=2, right_current=4, right_edge=2):
                    return []

            return EmptyPagination()

    def search_courses(self, query=None, skills=None, level=None,
                       price_max=None, page=1, per_page=20):
        """Поиск курсов с фильтрацией"""
        try:
            courses_query = Course.query

            if query and query.strip():
                search_term = f"%{query.strip()}%"
                courses_query = courses_query.filter(
                    (Course.title.ilike(search_term)) |
                    (Course.description.ilike(search_term)) |
                    (Course.provider.ilike(search_term))
                )
                print(f"Поиск курсов по запросу: {query}")

            if skills and len(skills) > 0 and skills[0]:
                print(f"Фильтр курсов по навыкам: {skills}")
                for skill_name in skills:
                    if skill_name and skill_name.strip():
                        courses_query = courses_query.filter(
                            Course.skills.any(name=skill_name)
                        )

            if level and level.strip():
                print(f"Фильтр по уровню: {level}")
                courses_query = courses_query.filter(Course.level == level)

            if price_max and price_max > 0:
                print(f"Фильтр по цене до: {price_max}")
                courses_query = courses_query.filter(Course.price <= price_max)

            courses_query = courses_query.order_by(Course.rating.desc())

            total = courses_query.count()
            print(f"Найдено курсов до пагинации: {total}")

            result = courses_query.paginate(page=page, per_page=per_page, error_out=False)

            print(f"Результаты курсов: страница {page}, показано {len(result.items)} из {result.total}")
            print(f"Всего страниц курсов: {result.pages}")

            return result

        except Exception as e:
            print(f"Ошибка при поиске курсов: {e}")
            import traceback
            traceback.print_exc()

            from flask_sqlalchemy import Pagination

            class EmptyPagination(Pagination):
                def __init__(self):
                    self.items = []
                    self.total = 0
                    self.pages = 0
                    self.page = page
                    self.per_page = per_page
                    self.has_prev = False
                    self.has_next = False
                    self.prev_num = None
                    self.next_num = None
                    self.query = None

                def iter_pages(self, left_edge=2, left_current=2, right_current=4, right_edge=2):
                    return []

            return EmptyPagination()

    def add_search_history(self, user_id, query, filters=None, content_type='vacancy'):
        """Добавление записи в историю поиска"""
        try:
            search = SearchHistory(
                user_id=user_id,
                query=query,
                filters=json.dumps(filters) if filters else None,
                content_type=content_type
            )
            self.db.session.add(search)
            self.db.session.commit()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении истории поиска: {e}")
            self.db.session.rollback()
            return False

    def add_view_history(self, user_id, content_id, content_type):
        """Добавление записи в историю просмотров"""
        try:
            view = ViewHistory(
                user_id=user_id,
                content_id=content_id,
                content_type=content_type
            )
            self.db.session.add(view)
            self.db.session.commit()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении истории просмотров: {e}")
            self.db.session.rollback()
            return False

    def get_user_history(self, user_id, days=30):
        """Получение истории пользователя за последние N дней"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            searches = SearchHistory.query.filter(
                SearchHistory.user_id == user_id,
                SearchHistory.created_at >= cutoff_date
            ).order_by(SearchHistory.created_at.desc()).all()

            views = ViewHistory.query.filter(
                ViewHistory.user_id == user_id,
                ViewHistory.viewed_at >= cutoff_date
            ).order_by(ViewHistory.viewed_at.desc()).all()

            return {'searches': searches, 'views': views}
        except Exception as e:
            print(f"Ошибка при получении истории: {e}")
            import traceback
            traceback.print_exc()
            return {'searches': [], 'views': []}