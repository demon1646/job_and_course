# app.py
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import warnings
import threading
import time
import uuid

warnings.filterwarnings('ignore')

from config import Config
from models import db, User, Skill, Vacancy, Course, SearchHistory, ViewHistory
from database import DatabaseManager
from scraper import JobScraper, CourseScraper
from recommender import RecommenderSystem

app = Flask(__name__)
app.config.from_object(Config)

# Исправление для Render PostgreSQL
if os.environ.get('DATABASE_URL'):
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'

# Инициализация менеджеров
db_manager = DatabaseManager()
recommender = RecommenderSystem()
job_scraper = JobScraper()
course_scraper = CourseScraper()

# Словарь для отслеживания статуса фоновых задач
background_tasks = {}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    """Главная страница со всеми вакансиями и курсами"""
    per_page = 10

    try:
        vacancies = Vacancy.query.order_by(Vacancy.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        courses = Course.query.order_by(Course.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        skills_count = Skill.query.count()
        users_count = User.query.count()

    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")

        class EmptyPagination:
            def __init__(self):
                self.items = []
                self.total = 0
                self.pages = 0
                self.page = 1
                self.has_prev = False
                self.has_next = False
                self.iter_pages = lambda: []

        vacancies = EmptyPagination()
        courses = EmptyPagination()
        skills_count = 0
        users_count = 0

    return render_template('index.html',
                           vacancies=vacancies,
                           courses=courses,
                           skills_count=skills_count,
                           users_count=users_count,
                           page=page)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователя"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('Все поля обязательны для заполнения')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован')
            return redirect(url_for('register'))

        try:
            user = db_manager.create_user(username, email, password)
            if user:
                login_user(user)
                flash('Регистрация прошла успешно!')
                return redirect(url_for('profile'))
            else:
                flash('Ошибка при создании пользователя')
                return redirect(url_for('register'))
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            flash('Произошла ошибка при регистрации')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход пользователя"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Добро пожаловать!')
            return redirect(next_page) if next_page else redirect(url_for('profile'))

        flash('Неверный email или пароль')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Профиль пользователя"""
    if request.method == 'POST':
        try:
            current_user.full_name = request.form.get('full_name')
            current_user.location = request.form.get('location')
            current_user.desired_position = request.form.get('desired_position')

            min_salary = request.form.get('min_salary')
            if min_salary:
                current_user.min_salary = int(min_salary)

            experience_years = request.form.get('experience_years')
            if experience_years:
                current_user.experience_years = int(experience_years)

            db.session.commit()
            flash('Профиль обновлен')
        except Exception as e:
            flash(f'Ошибка при обновлении профиля: {str(e)}')
            db.session.rollback()

        return redirect(url_for('profile'))

    profile_analysis = None
    recommended_vacancies = []
    recommended_courses = []
    history = {'searches': [], 'views': []}

    try:
        profile_analysis = recommender.analyze_user_profile(current_user.id)
    except Exception as e:
        print(f"Ошибка анализа профиля: {e}")

    try:
        recommended_vacancies = recommender.recommend_vacancies(current_user.id, limit=5)
    except Exception as e:
        print(f"Ошибка рекомендаций вакансий: {e}")

    try:
        recommended_courses = recommender.recommend_courses(current_user.id, limit=5)
    except Exception as e:
        print(f"Ошибка рекомендаций курсов: {e}")

    try:
        history = db_manager.get_user_history(current_user.id)
    except Exception as e:
        print(f"Ошибка получения истории: {e}")

    all_skills = Skill.query.all()

    return render_template('profile.html',
                           user=current_user,
                           analysis=profile_analysis,
                           recommended_vacancies=recommended_vacancies,
                           recommended_courses=recommended_courses,
                           history=history,
                           all_skills=all_skills)


@app.route('/search')
def search():
    """Поиск вакансий и курсов"""
    query = request.args.get('q', '')
    content_type = request.args.get('type', 'vacancy')
    page = request.args.get('page', 1, type=int)

    skills = request.args.getlist('skills')
    location = request.args.get('location')
    salary_min = request.args.get('salary_min', type=int)
    employment_type = request.args.get('employment_type')
    level = request.args.get('level')
    price_max = request.args.get('price_max', type=int)

    print(f"=== ПОИСК ====")
    print(f"Query: {query}")
    print(f"Type: {content_type}")
    print(f"Page: {page}")
    print(f"Skills: {skills}")
    print(f"Location: {location}")
    print(f"Salary min: {salary_min}")
    print(f"Employment type: {employment_type}")
    print(f"Level: {level}")
    print(f"Price max: {price_max}")

    history = {'searches': [], 'views': []}
    if current_user.is_authenticated:
        try:
            history = db_manager.get_user_history(current_user.id)
        except Exception as e:
            print(f"Ошибка получения истории: {e}")

    try:
        if content_type == 'vacancy':
            results = db_manager.search_vacancies(
                query=query,
                skills=skills,
                location=location,
                salary_min=salary_min,
                employment_type=employment_type,
                page=page,
                per_page=10
            )
        else:
            results = db_manager.search_courses(
                query=query,
                skills=skills,
                level=level,
                price_max=price_max,
                page=page,
                per_page=10
            )

        print(f"Результаты: всего {results.total}, на странице {len(results.items)}")
        print(f"Страниц всего: {results.pages}")
        print(f"Текущая страница: {results.page}")
        print(f"Есть предыдущая: {results.has_prev}")
        print(f"Есть следующая: {results.has_next}")

    except Exception as e:
        print(f"Ошибка поиска: {e}")
        import traceback
        traceback.print_exc()

        class EmptyResult:
            def __init__(self):
                self.items = []
                self.total = 0
                self.pages = 0
                self.page = page
                self.per_page = 10
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None

            def iter_pages(self, left_edge=2, left_current=2, right_current=4, right_edge=2):
                return []

        results = EmptyResult()

    if current_user.is_authenticated and query:
        try:
            filters = {
                'skills': skills,
                'location': location,
                'salary_min': salary_min,
                'employment_type': employment_type,
                'level': level,
                'price_max': price_max
            }
            db_manager.add_search_history(current_user.id, query, filters, content_type)
        except Exception as e:
            print(f"Ошибка сохранения истории поиска: {e}")

    all_skills = Skill.query.all()

    return render_template('search.html',
                           results=results,
                           query=query,
                           content_type=content_type,
                           skills=all_skills,
                           history=history)


@app.route('/vacancy/<int:vacancy_id>')
def vacancy_detail(vacancy_id):
    """Детальная страница вакансии"""
    vacancy = db.session.get(Vacancy, vacancy_id)
    if not vacancy:
        flash('Вакансия не найдена')
        return redirect(url_for('search'))

    if current_user.is_authenticated:
        try:
            db_manager.add_view_history(current_user.id, vacancy_id, 'vacancy')
            similar = recommender.content_based_recommendations(vacancy_id, 'vacancy', limit=3)
        except:
            similar = []
    else:
        similar = []

    return render_template('vacancy.html', vacancy=vacancy, similar=similar)


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    """Детальная страница курса"""
    course = db.session.get(Course, course_id)
    if not course:
        flash('Курс не найден')
        return redirect(url_for('search'))

    if current_user.is_authenticated:
        try:
            db_manager.add_view_history(current_user.id, course_id, 'course')
            similar = recommender.content_based_recommendations(course_id, 'course', limit=3)
        except:
            similar = []
    else:
        similar = []

    return render_template('course.html', course=course, similar=similar)


@app.route('/api/recommendations')
@login_required
def api_recommendations():
    """API для получения рекомендаций"""
    content_type = request.args.get('type', 'vacancy')
    limit = request.args.get('limit', 10, type=int)

    try:
        if content_type == 'vacancy':
            items = recommender.recommend_vacancies(current_user.id, limit)
            data = [{
                'id': item.id,
                'title': item.title,
                'company': item.company,
                'location': item.location,
                'salary': item.get_salary_display()
            } for item in items]
        else:
            items = recommender.recommend_courses(current_user.id, limit)
            data = [{
                'id': item.id,
                'title': item.title,
                'provider': item.provider,
                'rating': item.rating,
                'price': item.price
            } for item in items]
    except Exception as e:
        print(f"API recommendations error: {e}")
        data = []

    return jsonify(data)


@app.route('/api/analyze-profile')
@login_required
def api_analyze_profile():
    """API для анализа профиля"""
    try:
        analysis = recommender.analyze_user_profile(current_user.id)
        return jsonify(analysis)
    except Exception as e:
        print(f"API analyze error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/skills/add', methods=['POST'])
@login_required
def add_skill():
    """Добавление навыка пользователю"""
    skill_name = request.form.get('skill_name')

    if skill_name:
        try:
            skill = db_manager.add_skill(skill_name)
            db_manager.add_user_skill(current_user.id, skill.id, level=1)
            flash(f'Навык "{skill_name}" добавлен')
        except Exception as e:
            flash(f'Ошибка при добавлении навыка: {str(e)}')

    return redirect(url_for('profile'))


@app.route('/skills/remove/<int:skill_id>', methods=['POST'])
@login_required
def remove_skill(skill_id):
    """Удаление навыка пользователя"""
    skill = db.session.get(Skill, skill_id)
    if skill and skill in current_user.skills:
        current_user.skills.remove(skill)
        db.session.commit()
        flash(f'Навык "{skill.name}" удален')

    return redirect(url_for('profile'))


def run_update_task(task_id, update_type, data_type, categories=None):
    """Функция для выполнения обновления в фоновом потоке"""
    try:
        from update_data import update_data

        # Обновляем статус задачи
        background_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Запуск обновления...',
            'start_time': datetime.now().isoformat()
        }

        with app.app_context():
            # Обновляем прогресс
            background_tasks[task_id]['progress'] = 10
            background_tasks[task_id]['message'] = 'Инициализация парсеров...'

            # Запускаем обновление в зависимости от типа
            if data_type == 'vacancies':
                if update_type == 'quick':
                    background_tasks[task_id]['message'] = 'Быстрое обновление вакансий (IT)...'
                    update_data(quick=True, vacancies_only=True)
                elif update_type == 'categories' and categories:
                    background_tasks[task_id]['message'] = f'Обновление вакансий по категориям: {categories}...'
                    update_data(categories=categories, vacancies_only=True)
                else:
                    background_tasks[task_id]['message'] = 'Полное обновление всех вакансий...'
                    update_data(quick=False, vacancies_only=True)

            elif data_type == 'courses':
                if update_type == 'quick':
                    background_tasks[task_id]['message'] = 'Быстрое обновление курсов (IT)...'
                    update_data(quick=True, courses_only=True)
                elif update_type == 'categories' and categories:
                    background_tasks[task_id]['message'] = f'Обновление курсов по категориям: {categories}...'
                    update_data(categories=categories, courses_only=True)
                else:
                    background_tasks[task_id]['message'] = 'Полное обновление всех курсов...'
                    update_data(quick=False, courses_only=True)

            else:  # обновление всего
                if update_type == 'quick':
                    background_tasks[task_id]['message'] = 'Быстрое обновление всех данных (IT)...'
                    update_data(quick=True)
                elif update_type == 'categories' and categories:
                    background_tasks[task_id]['message'] = f'Обновление всех данных по категориям: {categories}...'
                    update_data(categories=categories)
                else:
                    background_tasks[task_id]['message'] = 'Полное обновление всех данных...'
                    update_data(quick=False)

            # Обновляем прогресс до 90%
            background_tasks[task_id]['progress'] = 90
            background_tasks[task_id]['message'] = 'Сохранение результатов...'
            time.sleep(1)

            # Завершаем задачу
            background_tasks[task_id]['status'] = 'completed'
            background_tasks[task_id]['progress'] = 100
            background_tasks[task_id]['message'] = 'Обновление успешно завершено!'
            background_tasks[task_id]['end_time'] = datetime.now().isoformat()

    except Exception as e:
        # В случае ошибки
        background_tasks[task_id]['status'] = 'error'
        background_tasks[task_id]['progress'] = 0
        background_tasks[task_id]['message'] = f'Ошибка: {str(e)}'
        background_tasks[task_id]['error'] = str(e)
        background_tasks[task_id]['end_time'] = datetime.now().isoformat()
        print(f"Ошибка в фоновой задаче {task_id}: {e}")
        import traceback
        traceback.print_exc()


@app.route('/api/update-data-background', methods=['POST'])
def api_update_data_background():
    """Запускает обновление данных в фоновом потоке"""
    try:
        update_type = request.form.get('type', 'quick')
        data_type = request.form.get('data_type', 'all')
        categories = request.form.get('categories')

        # Генерируем уникальный ID для задачи
        task_id = str(uuid.uuid4())

        # Преобразуем категории из JSON если есть
        cat_list = None
        if categories:
            import json
            cat_list = json.loads(categories)

        # Запускаем фоновый поток
        thread = threading.Thread(
            target=run_update_task,
            args=(task_id, update_type, data_type, cat_list)
        )
        thread.daemon = True  # Поток завершится при остановке приложения
        thread.start()

        # Сразу возвращаем ID задачи
        return jsonify({
            'status': 'started',
            'task_id': task_id,
            'message': 'Обновление запущено в фоновом режиме'
        })

    except Exception as e:
        print(f"Ошибка при запуске фоновой задачи: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/task-status/<task_id>', methods=['GET'])
def api_task_status(task_id):
    """Получение статуса фоновой задачи"""
    if task_id in background_tasks:
        return jsonify(background_tasks[task_id])
    else:
        return jsonify({'status': 'not_found', 'message': 'Задача не найдена'}), 404


@app.route('/api/cleanup-tasks', methods=['POST'])
def api_cleanup_tasks():
    """Очистка завершенных задач старше 1 часа"""
    try:
        current_time = datetime.now()
        to_delete = []

        for task_id, task in background_tasks.items():
            if task['status'] in ['completed', 'error']:
                if 'end_time' in task:
                    end_time = datetime.fromisoformat(task['end_time'])
                    # Удаляем задачи старше 1 часа
                    if (current_time - end_time).total_seconds() > 3600:
                        to_delete.append(task_id)

        for task_id in to_delete:
            del background_tasks[task_id]

        return jsonify({'deleted': len(to_delete)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data-status', methods=['GET'])
def api_data_status():
    """API для получения статуса данных"""
    try:
        vacancies = Vacancy.query.count()
        courses = Course.query.count()
        skills = Skill.query.count()
        users = User.query.count()

        # Последнее обновление
        last_update = None
        update_file = 'last_update.txt'
        if os.path.exists(update_file):
            with open(update_file, 'r') as f:
                last_update = f.read().strip()

        return jsonify({
            'vacancies': vacancies,
            'courses': courses,
            'skills': skills,
            'users': users,
            'last_update': last_update
        })
    except Exception as e:
        print(f"Ошибка получения статуса: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("=" * 60)
            print("🚀 JOB & COURSE FINDER")
            print("=" * 60)
            print(f"✅ База данных готова")
            print(f"📊 Вакансий: {Vacancy.query.count()}")
            print(f"📚 Курсов: {Course.query.count()}")
            print(f"🏷️  Навыков: {Skill.query.count()}")
            print(f"👤 Пользователей: {User.query.count()}")

            if Vacancy.query.count() == 0 and Course.query.count() == 0:
                print("\n⚠️  Данные отсутствуют!")
                print("   Для получения данных выполните:")
                print("   python update_data.py         # полное обновление")
                print("   python update_data.py --quick # быстрое обновление (IT)")
            else:
                print("\n✅ Данные загружены")
        except Exception as e:
            print(f"❌ Ошибка при создании базы данных: {e}")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
