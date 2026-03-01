# Job & Course Finder - Интеллектуальная система поиска вакансий и курсов


### Локальный запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/demon1646/job_and_course.git
cd job_and_course

# 2. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Инициализировать базу данных
python init_db.py

# 5. Запустить приложение
python app.py
