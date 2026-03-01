from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

vacancy_skills = db.Table('vacancy_skills',
                          db.Column('vacancy_id', db.Integer, db.ForeignKey('vacancies.id')),
                          db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'))
                          )

course_skills = db.Table('course_skills',
                         db.Column('course_id', db.Integer, db.ForeignKey('courses.id')),
                         db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'))
                         )

user_skills = db.Table('user_skills',
                       db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                       db.Column('skill_id', db.Integer, db.ForeignKey('skills.id')),
                       db.Column('level', db.Integer, default=1)
                       )


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    desired_position = db.Column(db.String(100))
    min_salary = db.Column(db.Integer)
    experience_years = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship('Skill', secondary=user_skills, backref=db.backref('users', lazy='dynamic'))
    search_history = db.relationship('SearchHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    view_history = db.relationship('ViewHistory', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_skills_list(self):
        return [skill.name for skill in self.skills]


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50))

    def __repr__(self):
        return f'<Skill {self.name}>'


class Vacancy(db.Model):
    __tablename__ = 'vacancies'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100))
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(3), default='RUB')
    location = db.Column(db.String(100))
    employment_type = db.Column(db.String(50))
    experience_required = db.Column(db.String(50))
    url = db.Column(db.String(500))
    source = db.Column(db.String(50))
    posted_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship('Skill', secondary=vacancy_skills, backref=db.backref('vacancies', lazy='dynamic'))

    def get_skills_list(self):
        return [skill.name for skill in self.skills]

    def get_salary_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_min} - {self.salary_max} {self.salary_currency}"
        elif self.salary_min:
            return f"от {self.salary_min} {self.salary_currency}"
        elif self.salary_max:
            return f"до {self.salary_max} {self.salary_currency}"
        return "Зарплата не указана"


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(100))
    description = db.Column(db.Text)
    duration = db.Column(db.String(50))
    level = db.Column(db.String(50))
    price = db.Column(db.Float)
    price_currency = db.Column(db.String(3), default='RUB')
    url = db.Column(db.String(500))
    source = db.Column(db.String(50))
    rating = db.Column(db.Float)
    students_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship('Skill', secondary=course_skills, backref=db.backref('courses', lazy='dynamic'))

    def get_skills_list(self):
        return [skill.name for skill in self.skills]


class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(200))
    filters = db.Column(db.JSON)
    content_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ViewHistory(db.Model):
    __tablename__ = 'view_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_id = db.Column(db.Integer)
    content_type = db.Column(db.String(20))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ViewHistory {self.user_id} - {self.content_type}:{self.content_id}>'