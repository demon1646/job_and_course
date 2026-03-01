import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import re



class BaseScraper:
    """Базовый класс для всех парсеров"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.delay = random.uniform(2, 4)

    def _make_request(self, url, params=None):
        """Выполнение HTTP запроса с обработкой ошибок"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response
            else:
                print(f"   ❌ Ошибка HTTP: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
            return None


class JobScraper(BaseScraper):
    """Парсер вакансий с различных сайтов для всех сфер"""

    def __init__(self):
        super().__init__()
        self.sources = {
            'hh.ru': self.parse_hh_vacancies,
            'habr.career': self.parse_habr_vacancies,
            'remoteok': self.parse_remoteok_vacancies,
            'trudvsem': self.parse_trudvsem_vacancies,
            'rabota.ru': self.parse_rabota_ru_vacancies,
            'superjob': self.parse_superjob_vacancies,
            'zarplata.ru': self.parse_zarplata_ru_vacancies,
        }

    def parse_all_sources(self, search_query, pages=1):
        """Парсинг со всех доступных источников"""
        all_vacancies = []

        print(f"\n{'=' * 60}")
        print(f"🔍 ПАРСИНГ ВАКАНСИЙ СО ВСЕХ ИСТОЧНИКОВ")
        print(f"Поисковый запрос: '{search_query}'")
        print(f"{'=' * 60}")

        for source_name, parser_func in self.sources.items():
            print(f"\n📌 Источник: {source_name}")
            try:
                vacancies = parser_func(search_query, pages)
                if vacancies:
                    print(f"   ✅ Получено вакансий: {len(vacancies)}")
                    all_vacancies.extend(vacancies)
                else:
                    print(f"   ⚠️ Вакансии не найдены")
            except Exception as e:
                print(f"   ❌ Ошибка парсинга: {e}")

            time.sleep(random.uniform(3, 5))

        return all_vacancies

    def parse_hh_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с hh.ru (все сферы)"""
        vacancies = []
        base_url = "https://hh.ru/search/vacancy"

        params = {
            'text': search_query,
            'area': 113,
            'search_field': 'name',
            'items_on_page': 20,
            'no_magic': 'true',
            'L_save_area': 'true',
            'clusters': 'true',
            'enable_snippets': 'true'
        }

        for page in range(pages):
            params['page'] = page
            response = self._make_request(base_url, params)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_cards = soup.find_all('div', {'data-qa': 'vacancy-serp__vacancy'})

            for card in vacancy_cards:
                try:
                    title_elem = card.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url = title_elem.get('href', '')

                    company_elem = card.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}) or \
                                   card.find('div', {'data-qa': 'vacancy-serp__vacancy-employer'})
                    company = company_elem.text.strip() if company_elem else 'Не указано'

                    salary_elem = card.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                    salary_min, salary_max, salary_currency = self._parse_salary(
                        salary_elem.text if salary_elem else '')

                    location_elem = card.find('span', {'data-qa': 'vacancy-serp__vacancy-address'})
                    location = location_elem.text.strip() if location_elem else 'Не указано'

                    category = self._detect_category(title + ' ' + company)

                    vacancy = {
                        'title': title,
                        'company': company,
                        'description': f"Вакансия {title} в компании {company}",
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency,
                        'location': location,
                        'employment_type': self._detect_employment_type(title),
                        'url': url,
                        'source': 'hh.ru',
                        'category': category,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

                except Exception as e:
                    continue

        return vacancies

    def parse_habr_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с Habr Career (IT и не только)"""
        vacancies = []
        base_url = "https://career.habr.com/vacancies"

        params = {
            'q': search_query,
            'type': 'all',
            'page': 1
        }

        for page in range(pages):
            params['page'] = page + 1
            response = self._make_request(base_url, params)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_cards = soup.find_all('div', {'class': 'vacancy-card'})

            for card in vacancy_cards:
                try:
                    title_elem = card.find('div', {'class': 'vacancy-card__title'})
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url = "https://career.habr.com" + title_elem.find('a').get('href', '')

                    company_elem = card.find('div', {'class': 'vacancy-card__company'})
                    company = company_elem.text.strip() if company_elem else 'Не указано'

                    salary_elem = card.find('div', {'class': 'vacancy-card__salary'})
                    salary_min, salary_max, salary_currency = self._parse_salary(
                        salary_elem.text if salary_elem else '')

                    meta_elem = card.find('div', {'class': 'vacancy-card__meta'})
                    location = meta_elem.text.strip() if meta_elem else 'Не указано'

                    skills_elem = card.find_all('span', {'class': 'vacancy-card__skills-item'})
                    skills = [s.text.strip() for s in skills_elem]

                    category = self._detect_category(title + ' ' + company + ' ' + ' '.join(skills))

                    vacancy = {
                        'title': title,
                        'company': company,
                        'description': f"Вакансия {title} в компании {company}. Требуемые навыки: {', '.join(skills)}",
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency,
                        'location': location,
                        'employment_type': 'full-time',
                        'url': url,
                        'source': 'habr.career',
                        'category': category,
                        'skills_list': skills,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

                except Exception as e:
                    continue

        return vacancies

    def parse_remoteok_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с RemoteOK (международные, все сферы)"""
        vacancies = []
        base_url = "https://remoteok.com/remote-jobs"

        params = {
            'search': search_query
        }

        response = self._make_request(base_url, params)
        if not response:
            return vacancies

        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('tr', {'class': 'job'})

        for card in job_cards[:20]:
            try:
                title_elem = card.find('h2', {'itemprop': 'title'})
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                company_elem = card.find('span', {'class': 'companyLink'})
                company = company_elem.text.strip() if company_elem else 'RemoteOK'

                if search_query.lower() not in title.lower() and search_query.lower() not in company.lower():
                    continue

                salary_elem = card.find('div', {'class': 'salary'})
                salary_min, salary_max, salary_currency = self._parse_salary(salary_elem.text if salary_elem else '')

                tags_elem = card.find_all('span', {'class': 'tag'})
                tags = [tag.text.strip() for tag in tags_elem]

                category = self._detect_category(title + ' ' + company + ' ' + ' '.join(tags))

                vacancy = {
                    'title': title,
                    'company': company,
                    'description': f"Remote вакансия: {title}. Теги: {', '.join(tags)}",
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'salary_currency': salary_currency or 'USD',
                    'location': 'Remote',
                    'employment_type': 'remote',
                    'url': "https://remoteok.com" + card.find('a').get('href', ''),
                    'source': 'remoteok',
                    'category': category,
                    'skills_list': tags,
                    'posted_date': datetime.now()
                }
                vacancies.append(vacancy)

            except Exception as e:
                continue

        return vacancies

    def parse_trudvsem_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с Работа в России (все сферы, гос. портал)"""
        vacancies = []
        base_url = "https://opendata.trudvsem.ru/api/v1/vacancies"

        params = {
            'text': search_query,
            'offset': 0,
            'limit': 20,
            'sort': 'asc'
        }

        for page in range(pages):
            params['offset'] = page * 20
            response = self._make_request(base_url, params)
            if not response:
                continue

            try:
                data = response.json()
                results = data.get('results', {}).get('vacancies', [])

                for item in results:
                    vacancy_data = item.get('vacancy', {})
                    company_data = vacancy_data.get('company', {})

                    title = vacancy_data.get('job-name', '')
                    if not title:
                        continue

                    category = self._detect_category(title + ' ' + vacancy_data.get('duty', ''))

                    vacancy = {
                        'title': title,
                        'company': company_data.get('company-name', 'Не указано'),
                        'description': vacancy_data.get('duty', ''),
                        'salary_min': self._extract_salary(vacancy_data.get('salary_min')),
                        'salary_max': self._extract_salary(vacancy_data.get('salary_max')),
                        'salary_currency': 'RUB',
                        'location': vacancy_data.get('region', {}).get('name', 'Не указано'),
                        'employment_type': self._detect_employment_type(vacancy_data.get('employment', '')),
                        'url': vacancy_data.get('vac_url', ''),
                        'source': 'trudvsem',
                        'category': category,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

            except Exception as e:
                print(f"   ❌ Ошибка парсинга trudvsem: {e}")

        return vacancies

    def parse_rabota_ru_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с Rabota.ru"""
        vacancies = []
        base_url = "https://www.rabota.ru/vacancy"

        params = {
            'query': search_query,
            'page': 1
        }

        for page in range(pages):
            params['page'] = page + 1
            response = self._make_request(base_url, params)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_cards = soup.find_all('div', {'class': 'vacancy-card'})

            for card in vacancy_cards:
                try:
                    title_elem = card.find('h3', {'class': 'vacancy-card__title'})
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url_elem = title_elem.find('a')
                    url = "https://www.rabota.ru" + url_elem.get('href', '') if url_elem else ''

                    company_elem = card.find('div', {'class': 'vacancy-card__company-name'})
                    company = company_elem.text.strip() if company_elem else 'Не указано'

                    salary_elem = card.find('div', {'class': 'vacancy-card__salary'})
                    salary_min, salary_max, salary_currency = self._parse_salary(
                        salary_elem.text if salary_elem else '')

                    location_elem = card.find('div', {'class': 'vacancy-card__address'})
                    location = location_elem.text.strip() if location_elem else 'Не указано'

                    category = self._detect_category(title + ' ' + company)

                    vacancy = {
                        'title': title,
                        'company': company,
                        'description': f"Вакансия на Rabota.ru: {title}",
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency,
                        'location': location,
                        'employment_type': 'full-time',
                        'url': url,
                        'source': 'rabota.ru',
                        'category': category,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

                except Exception as e:
                    continue

        return vacancies

    def parse_superjob_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с SuperJob (все сферы)"""
        vacancies = []
        base_url = "https://www.superjob.ru/vacancy/search/"

        params = {
            'keywords': search_query,
            'page': 1
        }

        for page in range(pages):
            params['page'] = page + 1
            response = self._make_request(base_url, params)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_cards = soup.find_all('div', {'class': 'f-test-search-result-item'})

            for card in vacancy_cards:
                try:
                    title_elem = card.find('span', {'class': '_1e6dO _1XzFs'})
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url_elem = title_elem.find('a')
                    url = "https://www.superjob.ru" + url_elem.get('href', '') if url_elem else ''

                    company_elem = card.find('span', {'class': '_1e6dO _2nzZn _1qx7q'})
                    company = company_elem.text.strip() if company_elem else 'Не указано'

                    salary_elem = card.find('span', {'class': '_2eYAG _1nqY_ _1qx7q'})
                    salary_min, salary_max, salary_currency = self._parse_salary(
                        salary_elem.text if salary_elem else '')

                    location_elem = card.find('span', {'class': '_1e6dO _2nzZn _1qx7q'})
                    location = location_elem.text.strip() if location_elem else 'Не указано'

                    category = self._detect_category(title + ' ' + company)

                    vacancy = {
                        'title': title,
                        'company': company,
                        'description': f"Вакансия на SuperJob: {title}",
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency,
                        'location': location,
                        'employment_type': 'full-time',
                        'url': url,
                        'source': 'superjob',
                        'category': category,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

                except Exception as e:
                    continue

        return vacancies

    def parse_zarplata_ru_vacancies(self, search_query, pages=1):
        """Парсинг вакансий с Zarplata.ru"""
        vacancies = []
        base_url = "https://www.zarplata.ru/vacancy"

        params = {
            'text': search_query,
            'page': 1
        }

        for page in range(pages):
            params['page'] = page + 1
            response = self._make_request(base_url, params)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            vacancy_cards = soup.find_all('div', {'class': 'vacancy-serp-item'})

            for card in vacancy_cards:
                try:
                    title_elem = card.find('a', {'class': 'vacancy-serp-item__title'})
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    url = title_elem.get('href', '')

                    company_elem = card.find('div', {'class': 'vacancy-serp-item__company-name'})
                    company = company_elem.text.strip() if company_elem else 'Не указано'

                    salary_elem = card.find('div', {'class': 'vacancy-serp-item__salary'})
                    salary_min, salary_max, salary_currency = self._parse_salary(
                        salary_elem.text if salary_elem else '')

                    location_elem = card.find('div', {'class': 'vacancy-serp-item__address'})
                    location = location_elem.text.strip() if location_elem else 'Не указано'

                    category = self._detect_category(title + ' ' + company)

                    vacancy = {
                        'title': title,
                        'company': company,
                        'description': f"Вакансия на Zarplata.ru: {title}",
                        'salary_min': salary_min,
                        'salary_max': salary_max,
                        'salary_currency': salary_currency,
                        'location': location,
                        'employment_type': 'full-time',
                        'url': url,
                        'source': 'zarplata.ru',
                        'category': category,
                        'posted_date': datetime.now()
                    }
                    vacancies.append(vacancy)

                except Exception as e:
                    continue

        return vacancies

    def _detect_category(self, text):
        """Определение категории вакансии по тексту"""
        text_lower = text.lower()

        categories = {
            'it': ['программист', 'разработчик', 'developer', 'software', 'python', 'java', 'javascript',
                   'frontend', 'backend', 'fullstack', 'devops', 'qa', 'тестировщик', 'аналитик', 'data scientist',
                   'системный администратор', 'сисадмин', 'dba', 'баз данных', 'web', 'сайт', '1с', '1с:предприятие'],

            'medicine': ['врач', 'медсестра', 'медицинский', 'фельдшер', 'хирург', 'терапевт', 'педиатр',
                         'стоматолог', 'фармацевт', 'аптека', 'больница', 'поликлиника', 'здравоохранение'],

            'education': ['учитель', 'преподаватель', 'педагог', 'воспитатель', 'тренер', 'репетитор',
                          'школа', 'детский сад', 'университет', 'институт', 'образование', 'обучение'],

            'finance': ['бухгалтер', 'экономист', 'финансист', 'аудитор', 'казначей', 'банк', 'инвестиции',
                        'кредит', 'страхование', 'налоги', 'финансовый аналитик', 'accountant'],

            'sales': ['продавец', 'менеджер по продажам', 'торговый представитель', 'кассир', 'мерчендайзер',
                      'супервайзер', 'коммивояжер', 'продажи', 'торговля'],

            'construction': ['строитель', 'инженер', 'архитектор', 'прораб', 'монтажник', 'отделочник',
                             'сантехник', 'электрик', 'сварщик', 'плотник', 'каменщик', 'строительство'],

            'transport': ['водитель', 'логист', 'экспедитор', 'дальнобойщик', 'курьер', 'перевозки',
                          'такси', 'автобус', 'транспорт', 'доставка'],

            'service': ['официант', 'бармен', 'повар', 'администратор', 'уборщица', 'горничная',
                        'хостес', 'ресепшен', 'обслуживание', 'сервис'],

            'management': ['директор', 'руководитель', 'начальник', 'управляющий', 'менеджер',
                           'супервайзер', 'заведующий', 'административный'],

            'marketing': ['маркетолог', 'pr', 'реклама', 'пиар', 'smm', 'маркетинг', 'продвижение',
                          'бренд-менеджер', 'маркетинговый'],

            'hr': ['hr', 'кадровик', 'рекрутер', 'подбор персонала', 'управление персоналом'],

            'design': ['дизайнер', 'оформитель', 'верстальщик', 'художник', 'графический дизайн',
                       'веб-дизайн', 'интерфейсы', 'ui', 'ux'],

            'law': ['юрист', 'адвокат', 'нотариус', 'правовед', 'закон', 'юридический', 'правовой'],

            'manufacturing': ['рабочий', 'производство', 'оператор', 'станочник', 'фрезеровщик',
                              'токарь', 'слесарь', 'завод', 'фабрика', 'цех']
        }

        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return 'other'

    def _parse_salary(self, salary_text):
        """Парсинг зарплаты из текста"""
        salary_min = None
        salary_max = None
        salary_currency = 'RUB'

        if not salary_text:
            return salary_min, salary_max, salary_currency

        if '$' in salary_text:
            salary_currency = 'USD'
        elif '€' in salary_text:
            salary_currency = 'EUR'
        elif '₽' in salary_text or 'руб' in salary_text.lower():
            salary_currency = 'RUB'

        numbers = re.findall(r'(\d{1,3}(?:\s?\d{3})*)', salary_text)
        numbers = [int(n.replace(' ', '')) for n in numbers]

        if '–' in salary_text or '—' in salary_text or '-' in salary_text:
            if len(numbers) >= 2:
                salary_min = numbers[0]
                salary_max = numbers[1]
        elif 'от' in salary_text.lower() and numbers:
            salary_min = numbers[0]
        elif 'до' in salary_text.lower() and numbers:
            salary_max = numbers[0]

        return salary_min, salary_max, salary_currency

    def _extract_salary(self, salary_value):
        """Извлечение числа из зарплаты"""
        if not salary_value:
            return None
        try:
            return int(float(salary_value))
        except:
            return None

    def _detect_employment_type(self, text):
        """Определение типа занятости из текста"""
        text_lower = text.lower()
        if 'remote' in text_lower or 'удален' in text_lower:
            return 'remote'
        elif 'part' in text_lower or 'частичн' in text_lower:
            return 'part-time'
        else:
            return 'full-time'


class CourseScraper(BaseScraper):
    """Парсер курсов с различных платформ для всех сфер"""

    def __init__(self):
        super().__init__()
        self.sources = {
            'stepik': self.parse_stepik_courses,
            'coursera': self.parse_coursera_courses,
            'udemy': self.parse_udemy_courses,
            'openedu': self.parse_openedu_courses,
            'lektorium': self.parse_lektorium_courses,
            'intuit': self.parse_intuit_courses,
            'universarium': self.parse_universarium_courses,
        }

    def parse_all_sources(self, search_query, pages=1):
        """Парсинг курсов со всех доступных источников"""
        all_courses = []

        print(f"\n{'=' * 60}")
        print(f"🔍 ПАРСИНГ КУРСОВ СО ВСЕХ ИСТОЧНИКОВ")
        print(f"Поисковый запрос: '{search_query}'")
        print(f"{'=' * 60}")

        for source_name, parser_func in self.sources.items():
            print(f"\n📌 Платформа: {source_name}")
            try:
                courses = parser_func(search_query, pages)
                if courses:
                    print(f"   ✅ Получено курсов: {len(courses)}")
                    all_courses.extend(courses)
                else:
                    print(f"   ⚠️ Курсы не найдены")
            except Exception as e:
                print(f"   ❌ Ошибка парсинга: {e}")

            time.sleep(random.uniform(2, 4))

        return all_courses

    def parse_stepik_courses(self, search_query, pages=1):
        """Парсинг курсов с Stepik (все темы)"""
        courses = []
        base_url = "https://stepik.org/api/courses"

        params = {
            'page': 1,
            'query': search_query,
            'is_public': 'true',
            'order': '-activity'
        }

        for page in range(pages):
            params['page'] = page + 1
            response = self._make_request(base_url, params)
            if not response:
                continue

            try:
                data = response.json()
                courses_data = data.get('courses', [])

                for course_data in courses_data:
                    title = course_data.get('title', '')
                    if not title:
                        continue

                    category = self._detect_course_category(title + ' ' + course_data.get('summary', ''))

                    course = {
                        'title': title,
                        'provider': 'Stepik',
                        'description': course_data.get('summary', '')[:500],
                        'level': self._detect_level(title),
                        'url': f"https://stepik.org/course/{course_data.get('id')}",
                        'source': 'stepik',
                        'students_count': course_data.get('learners_count', 0),
                        'rating': course_data.get('rating', 4.5),
                        'price': 0,
                        'category': category
                    }
                    courses.append(course)

            except Exception as e:
                print(f"   ❌ Ошибка парсинга Stepik: {e}")

        return courses

    def parse_coursera_courses(self, search_query, pages=1):
        """Парсинг курсов с Coursera (все темы)"""
        courses = []
        base_url = "https://www.coursera.org/api/catalogResults.v2"

        params = {
            'q': 'search',
            'query': search_query,
            'limit': 20
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        try:
            data = response.json()
            elements = data.get('elements', [])

            for element in elements[:15]:
                course_data = element.get('course', {})
                title = course_data.get('name', '')
                if not title:
                    continue

                category = self._detect_course_category(title + ' ' + course_data.get('description', ''))

                course = {
                    'title': title,
                    'provider': 'Coursera',
                    'description': course_data.get('description', '')[:500],
                    'level': self._detect_level(title),
                    'url': f"https://www.coursera.org/learn/{course_data.get('slug', '')}",
                    'source': 'coursera',
                    'rating': random.uniform(4.0, 4.9),
                    'price': 0,
                    'category': category
                }
                courses.append(course)
        except:
            pass

        return courses

    def parse_udemy_courses(self, search_query, pages=1):
        """Парсинг курсов с Udemy (все темы)"""
        courses = []
        base_url = "https://www.udemy.com/api-2.0/courses/"

        params = {
            'search': search_query,
            'page': 1,
            'page_size': 20,
            'language': 'ru'
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        try:
            data = response.json()
            results = data.get('results', [])

            for course_data in results[:15]:
                title = course_data.get('title', '')
                if not title:
                    continue

                category = self._detect_course_category(title + ' ' + course_data.get('headline', ''))

                course = {
                    'title': title,
                    'provider': 'Udemy',
                    'description': course_data.get('headline', '')[:500],
                    'level': self._detect_level(title),
                    'url': f"https://www.udemy.com{course_data.get('url', '')}",
                    'source': 'udemy',
                    'rating': course_data.get('avg_rating', 4.5),
                    'students_count': course_data.get('num_subscribers', 0),
                    'price': course_data.get('price', {}).get('amount', 1999),
                    'category': category
                }
                courses.append(course)
        except:
            pass

        return courses

    def parse_openedu_courses(self, search_query, pages=1):
        """Парсинг курсов с OpenEdu (российская платформа, все темы)"""
        courses = []
        base_url = "https://openedu.ru/api/courses"

        params = {
            'search': search_query
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        try:
            data = response.json()
            courses_data = data.get('courses', [])

            for course_data in courses_data[:20]:
                title = course_data.get('title', '')
                if not title:
                    continue

                category = self._detect_course_category(title + ' ' + course_data.get('description', ''))

                course = {
                    'title': title,
                    'provider': 'OpenEdu',
                    'description': course_data.get('description', '')[:500],
                    'level': self._detect_level(title),
                    'url': course_data.get('url', ''),
                    'source': 'openedu',
                    'price': 0,
                    'rating': 4.5,
                    'category': category
                }
                courses.append(course)
        except:
            pass

        return courses

    def parse_lektorium_courses(self, search_query, pages=1):
        """Парсинг курсов с Lektorium (все темы)"""
        courses = []
        base_url = "https://www.lektorium.tv/courses"

        params = {
            'keys': search_query,
            'page': 1
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        soup = BeautifulSoup(response.text, 'html.parser')
        course_cards = soup.find_all('div', {'class': 'views-row'})

        for card in course_cards[:15]:
            try:
                title_elem = card.find('h3')
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                url_elem = title_elem.find('a')
                url = "https://www.lektorium.tv" + url_elem.get('href', '') if url_elem else ''

                category = self._detect_course_category(title)

                course = {
                    'title': title,
                    'provider': 'Lektorium',
                    'description': f"Курс на платформе Lektorium: {title}",
                    'level': self._detect_level(title),
                    'url': url,
                    'source': 'lektorium',
                    'price': 0,
                    'rating': 4.3,
                    'category': category
                }
                courses.append(course)

            except Exception as e:
                continue

        return courses

    def parse_intuit_courses(self, search_query, pages=1):
        """Парсинг курсов с Intuit.ru (все темы)"""
        courses = []
        base_url = "https://intuit.ru/search"

        params = {
            'q': search_query,
            'page': 1
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        soup = BeautifulSoup(response.text, 'html.parser')
        course_cards = soup.find_all('div', {'class': 'search-item'})

        for card in course_cards[:15]:
            try:
                title_elem = card.find('a', {'class': 'search-item-title'})
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                url = "https://intuit.ru" + title_elem.get('href', '')

                category = self._detect_course_category(title)

                course = {
                    'title': title,
                    'provider': 'Intuit',
                    'description': f"Курс на Intuit.ru: {title}",
                    'level': self._detect_level(title),
                    'url': url,
                    'source': 'intuit',
                    'price': 0,
                    'rating': 4.4,
                    'category': category
                }
                courses.append(course)

            except Exception as e:
                continue

        return courses

    def parse_universarium_courses(self, search_query, pages=1):
        """Парсинг курсов с Universarium (все темы)"""
        courses = []
        base_url = "https://universarium.org/catalog"

        params = {
            'search': search_query
        }

        response = self._make_request(base_url, params)
        if not response:
            return courses

        soup = BeautifulSoup(response.text, 'html.parser')
        course_cards = soup.find_all('div', {'class': 'course-card'})

        for card in course_cards[:15]:
            try:
                title_elem = card.find('div', {'class': 'course-card__title'})
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                url_elem = card.find('a', {'class': 'course-card__link'})
                url = "https://universarium.org" + url_elem.get('href', '') if url_elem else ''

                category = self._detect_course_category(title)

                course = {
                    'title': title,
                    'provider': 'Universarium',
                    'description': f"Курс на Universarium: {title}",
                    'level': self._detect_level(title),
                    'url': url,
                    'source': 'universarium',
                    'price': 0,
                    'rating': 4.2,
                    'category': category
                }
                courses.append(course)

            except Exception as e:
                continue

        return courses

    def _detect_course_category(self, text):
        """Определение категории курса по тексту"""
        text_lower = text.lower()

        categories = {
            'programming': ['программирование', 'python', 'java', 'javascript', 'c++', 'разработка',
                            'web', 'сайт', 'алгоритмы', 'базы данных', 'sql'],

            'data_science': ['data science', 'машинное обучение', 'анализ данных', 'нейросети',
                             'big data', 'статистика', 'аналитика'],

            'business': ['бизнес', 'управление', 'менеджмент', 'маркетинг', 'продажи', 'реклама',
                         'предпринимательство', 'стартап'],

            'design': ['дизайн', 'графика', 'photoshop', 'illustrator', 'figma', '3d', 'анимация'],

            'languages': ['английский', 'немецкий', 'французский', 'испанский', 'китайский',
                          'язык', 'иностранный'],

            'medicine': ['медицина', 'здоровье', 'фармация', 'биология', 'химия', 'анатомия'],

            'education': ['педагогика', 'психология', 'образование', 'обучение', 'воспитание'],

            'finance': ['финансы', 'бухгалтерия', 'налоги', 'инвестиции', 'экономика'],

            'humanities': ['история', 'философия', 'культура', 'искусство', 'литература', 'языкознание'],

            'engineering': ['инженерия', 'строительство', 'электроника', 'робототехника', 'механика']
        }

        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return 'other'

    def _detect_level(self, title):
        """Определение уровня курса по названию"""
        title_lower = title.lower()
        if any(word in title_lower for word in
               ['beginner', 'начальный', 'основы', 'для начинающих', 'введение', 'intro']):
            return 'beginner'
        elif any(
                word in title_lower for word in ['advanced', 'продвинутый', 'эксперт', 'профессионал', 'professional']):
            return 'advanced'
        else:
            return 'intermediate'