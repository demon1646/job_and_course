# manage.py
# !/usr/bin/env python
import argparse
import os
import sys


def print_status():
    """Показать статус базы данных"""
    os.system(
        'python -c "from app import app; from models import Vacancy, Course, Skill, User; with app.app_context(): print(f\'📊 Вакансий: {Vacancy.query.count()}\'); print(f\'📚 Курсов: {Course.query.count()}\'); print(f\'🏷️  Навыков: {Skill.query.count()}\'); print(f\'👤 Пользователей: {User.query.count()}\')"')


def main():
    parser = argparse.ArgumentParser(description='Управление проектом Job Course Finder')
    parser.add_argument('command', choices=['start', 'update', 'init', 'status', 'shell'],
                        help='Команда для выполнения')
    parser.add_argument('--quick', action='store_true', help='Быстрое обновление')
    parser.add_argument('--categories', nargs='+', help='Категории для обновления')

    args = parser.parse_args()

    if args.command == 'start':
        print("🚀 Запуск приложения...")
        os.system('python app.py')

    elif args.command == 'update':
        if args.quick:
            print("⚡ Быстрое обновление (только IT)...")
            os.system('python update_data.py --quick')
        elif args.categories:
            print(f"🔍 Обновление категорий: {args.categories}")
            os.system(f'python update_data.py --categories {" ".join(args.categories)}')
        else:
            print("🔄 Полное обновление всех данных...")
            os.system('python update_data.py')

    elif args.command == 'init':
        print("🔄 Инициализация структуры базы данных...")
        os.system('python init_db.py')

    elif args.command == 'status':
        print("📊 Статус базы данных:")
        print_status()

    elif args.command == 'shell':
        print("🐚 Запуск Python shell...")
        os.system('python')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()