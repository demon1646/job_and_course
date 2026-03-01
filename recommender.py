from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import User, Vacancy, Course, ViewHistory
from collections import Counter



class RecommenderSystem:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

    def get_user_profile_vector(self, user_id):
        """Создание профиля пользователя на основе навыков и истории"""
        from app import db

        user = User.query.get(user_id)
        if not user:
            return None

        user_skills = [skill.name for skill in user.skills]

        viewed_vacancies = []
        viewed_courses = []

        try:
            viewed_vacancies = db.session.query(Vacancy).join(
                ViewHistory, ViewHistory.content_id == Vacancy.id
            ).filter(
                ViewHistory.user_id == user_id,
                ViewHistory.content_type == 'vacancy'
            ).limit(20).all()
        except Exception as e:
            print(f"Ошибка при получении истории вакансий: {e}")

        try:
            viewed_courses = db.session.query(Course).join(
                ViewHistory, ViewHistory.content_id == Course.id
            ).filter(
                ViewHistory.user_id == user_id,
                ViewHistory.content_type == 'course'
            ).limit(20).all()
        except Exception as e:
            print(f"Ошибка при получении истории курсов: {e}")

        viewed_skills = []
        for vacancy in viewed_vacancies:
            viewed_skills.extend([skill.name for skill in vacancy.skills])

        for course in viewed_courses:
            viewed_skills.extend([skill.name for skill in course.skills])

        all_skills = user_skills * 3 + viewed_skills
        if not all_skills:
            return Counter()

        skill_weights = Counter(all_skills)
        return skill_weights

    def recommend_vacancies(self, user_id, limit=10):
        """Рекомендация вакансий на основе профиля пользователя"""
        try:
            user_profile = self.get_user_profile_vector(user_id)
            if not user_profile:
                return []

            vacancies = Vacancy.query.all()

            recommendations = []
            for vacancy in vacancies:
                vacancy_skills = [skill.name for skill in vacancy.skills]

                if not vacancy_skills:
                    continue

                score = 0
                for skill, weight in user_profile.items():
                    if skill in vacancy_skills:
                        score += weight

                if vacancy_skills:
                    score = score / len(vacancy_skills)

                recommendations.append((vacancy, score))

            recommendations.sort(key=lambda x: x[1], reverse=True)

            return [vac for vac, score in recommendations[:limit]]
        except Exception as e:
            print(f"Ошибка при рекомендации вакансий: {e}")
            return []

    def recommend_courses(self, user_id, limit=10):
        """Рекомендация курсов на основе профиля пользователя"""
        try:
            user_profile = self.get_user_profile_vector(user_id)
            if not user_profile:
                return []

            courses = Course.query.all()

            recommendations = []
            for course in courses:
                course_skills = [skill.name for skill in course.skills]

                if not course_skills:
                    continue

                score = 0
                for skill, weight in user_profile.items():
                    if skill in course_skills:
                        score += weight

                if course_skills:
                    score = score / len(course_skills)

                recommendations.append((course, score))

            recommendations.sort(key=lambda x: x[1], reverse=True)

            return [course for course, score in recommendations[:limit]]
        except Exception as e:
            print(f"Ошибка при рекомендации курсов: {e}")
            return []

    def content_based_recommendations(self, item_id, content_type, limit=5):
        """Рекомендации на основе контента (похожие вакансии/курсы)"""
        try:
            if content_type == 'vacancy':
                item = Vacancy.query.get(item_id)
                if not item:
                    return []

                items = Vacancy.query.all()
                texts = [f"{v.title} {v.description} {' '.join([s.name for s in v.skills])}"
                         for v in items]

            elif content_type == 'course':
                item = Course.query.get(item_id)
                if not item:
                    return []

                items = Course.query.all()
                texts = [f"{c.title} {c.description} {' '.join([s.name for s in c.skills])}"
                         for c in items]
            else:
                return []

            if len(texts) < 2:
                return []

            tfidf_matrix = self.vectorizer.fit_transform(texts)

            try:
                item_index = items.index(item)
            except ValueError:
                return []

            cosine_sim = cosine_similarity(tfidf_matrix[item_index:item_index + 1], tfidf_matrix).flatten()

            similar_indices = cosine_sim.argsort()[:-limit - 2:-1]
            similar_indices = [i for i in similar_indices if i != item_index][:limit]

            return [items[i] for i in similar_indices]
        except Exception as e:
            print(f"Ошибка в content_based_recommendations: {e}")
            return []

    def analyze_user_profile(self, user_id):
        """Анализ профиля пользователя для статистики"""
        try:
            from app import db

            user = User.query.get(user_id)
            if not user:
                return None

            analysis = {
                'total_skills': len(user.skills),
                'top_skills': [skill.name for skill in user.skills[:5]],
                'experience_years': user.experience_years,
                'desired_position': user.desired_position,
                'skill_gaps': [],
                'recommended_career_path': []
            }

            if user.desired_position:
                target_vacancies = Vacancy.query.filter(
                    Vacancy.title.ilike(f'%{user.desired_position}%')
                ).limit(20).all()

                if target_vacancies:
                    required_skills = set()
                    for vac in target_vacancies:
                        for skill in vac.skills:
                            required_skills.add(skill.name)

                    user_skill_set = set([skill.name for skill in user.skills])
                    analysis['skill_gaps'] = list(required_skills - user_skill_set)[:10]

            try:
                viewed_vacancies = db.session.query(Vacancy).join(
                    ViewHistory, ViewHistory.content_id == Vacancy.id
                ).filter(
                    ViewHistory.user_id == user_id,
                    ViewHistory.content_type == 'vacancy'
                ).all()

                if viewed_vacancies:
                    positions = []
                    for vac in viewed_vacancies:
                        pos = vac.title.split(',')[0].strip()
                        if pos:
                            positions.append(pos)

                    if positions:
                        position_counter = Counter(positions)
                        analysis['recommended_career_path'] = [pos for pos, _ in position_counter.most_common(3)]
            except Exception as e:
                print(f"Ошибка при анализе карьерного пути: {e}")

            return analysis
        except Exception as e:
            print(f"Ошибка в analyze_user_profile: {e}")
            return {
                'total_skills': 0,
                'top_skills': [],
                'experience_years': 0,
                'desired_position': '',
                'skill_gaps': [],
                'recommended_career_path': []
            }