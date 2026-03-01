# init_db.py
from app import app
from models import db, Skill, User
import os


def init_database():
    """Инициализация структуры базы данных (без данных)"""
    with app.app_context():
        print("=" * 60)
        print("🔄 ИНИЦИАЛИЗАЦИЯ СТРУКТУРЫ БАЗЫ ДАННЫХ")
        print("=" * 60)

        # Создаем таблицы
        db.create_all()
        print("✅ Таблицы созданы")

        # Добавляем базовые навыки (только если их нет)
        if Skill.query.count() == 0:
            add_base_skills()
        else:
            print(f"✅ Навыки уже существуют: {Skill.query.count()}")

        # Создаем тестового пользователя (только если его нет)
        if User.query.count() == 0:
            create_test_user()
        else:
            print(f"✅ Пользователи уже существуют: {User.query.count()}")

        print("\n" + "=" * 60)
        print("✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)
        print(f"📊 Вакансий: {Vacancy.query.count()}")
        print(f"📚 Курсов: {Course.query.count()}")
        print(f"🏷️  Навыков: {Skill.query.count()}")
        print(f"👤 Пользователей: {User.query.count()}")
        print("\n⚠️  Данные отсутствуют. Запустите update_data.py для парсинга.")


def add_base_skills():
    """Добавление базовых навыков (только справочник)"""
    skills_data = [
        ('Python', 'programming'), ('JavaScript', 'programming'),
        ('Java', 'programming'), ('SQL', 'database'),
        ('React', 'frontend'), ('Django', 'backend'),
        ('Machine Learning', 'data science'), ('Docker', 'devops'),
        ('Git', 'tools'), ('Linux', 'system'),
        ('AWS', 'cloud'), ('Node.js', 'backend'),
        ('TypeScript', 'programming'), ('MongoDB', 'database'),
        ('PostgreSQL', 'database'), ('Redis', 'database'),
        ('Kubernetes', 'devops'), ('TensorFlow', 'data science'),
        ('Pandas', 'data science'), ('Flask', 'backend'),
        ('HTML', 'frontend'), ('CSS', 'frontend'),
        ('C++', 'programming'), ('C#', 'programming'),
        ('PHP', 'programming'), ('Ruby', 'programming'),
        ('Go', 'programming'), ('Swift', 'mobile'),
        ('Kotlin', 'mobile'), ('1C', 'enterprise'),
        ('Bitrix', 'cms'), ('WordPress', 'cms'),
        ('Spring', 'framework'), ('Express.js', 'framework'),
        ('Angular', 'frontend'), ('Vue.js', 'frontend'),
        ('Scikit-learn', 'data science'), ('Data Analysis', 'data science'),
        ('Медицина', 'medicine'), ('Педагогика', 'education'),
        ('Бухгалтерия', 'finance'), ('Менеджмент', 'management'),
        ('Маркетинг', 'marketing'), ('Дизайн', 'design'),
        ('Право', 'law'), ('Логистика', 'transport'),
        ('Строительство', 'construction'), ('Продажи', 'sales'),
        ('Обслуживание', 'service'), ('Управление', 'management'),
        ('HR', 'hr'), ('Юриспруденция', 'law'),
        ('Производство', 'manufacturing'), ('Сельское хозяйство', 'agriculture')
    ]

    for skill_name, category in skills_data:
        if not Skill.query.filter_by(name=skill_name).first():
            skill = Skill(name=skill_name, category=category)
            db.session.add(skill)

    db.session.commit()
    print(f"✅ Добавлено навыков: {Skill.query.count()}")


def create_test_user():
    """Создание тестового пользователя"""
    try:
        if not User.query.filter_by(username="test_user").first():
            test_user = User(
                username="test_user",
                email="test@example.com",
                full_name="Тестовый Пользователь",
                location="Москва",
                desired_position="Python Developer",
                min_salary=150000,
                experience_years=3
            )
            test_user.set_password("test123")
            db.session.add(test_user)
            db.session.commit()

            # Добавляем базовые навыки пользователю
            skills_to_add = ['Python', 'SQL', 'Git', 'Linux']
            for skill_name in skills_to_add:
                skill = Skill.query.filter_by(name=skill_name).first()
                if skill and skill not in test_user.skills:
                    test_user.skills.append(skill)

            db.session.commit()
            print("\n✅ Создан тестовый пользователь:")
            print("   Логин: test_user")
            print("   Пароль: test123")

    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")


if __name__ == '__main__':
    from models import Vacancy, Course

    init_database()