$(document).ready(function() {
    $('.card, .list-group-item, .alert').addClass('fade-in');

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    if ($('#recommendations-container').length) {
        loadRecommendations();
    }

    if ($('#search-input').length) {
        setupSearchAutocomplete();
    }

    highlightSelectedSkills();
    setupSmoothScroll();
});

function setupSearchAutocomplete() {
    $('#search-input').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/api/search-suggestions',
                data: { q: request.term },
                success: function(data) {
                    response(data);
                },
                error: function() {
                    response([]);
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $('#search-input').val(ui.item.value);
            $('#search-form').submit();
        }
    });
}

function highlightSelectedSkills() {
    $('.form-check-input:checked').each(function() {
        $(this).closest('.form-check').addClass('bg-light');
    });

    $('.form-check-input').change(function() {
        if ($(this).is(':checked')) {
            $(this).closest('.form-check').addClass('bg-light');
        } else {
            $(this).closest('.form-check').removeClass('bg-light');
        }

        $(this).closest('.form-check').addClass('pulse');
        setTimeout(() => {
            $(this).closest('.form-check').removeClass('pulse');
        }, 300);
    });
}

function loadRecommendations() {
    $.ajax({
        url: '/api/recommendations',
        method: 'GET',
        data: { type: 'vacancy', limit: 5 },
        success: function(data) {
            displayRecommendations(data, 'vacancy');
        },
        error: function() {
            $('#vacancy-recommendations').html('<div class="alert alert-warning">Не удалось загрузить рекомендации</div>');
        }
    });

    $.ajax({
        url: '/api/recommendations',
        method: 'GET',
        data: { type: 'course', limit: 5 },
        success: function(data) {
            displayRecommendations(data, 'course');
        },
        error: function() {
            $('#course-recommendations').html('<div class="alert alert-warning">Не удалось загрузить рекомендации</div>');
        }
    });
}

function displayRecommendations(items, type) {
    let container = type === 'vacancy' ? '#vacancy-recommendations' : '#course-recommendations';

    if (items.length === 0) {
        $(container).html(`
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                Пока нет рекомендаций. Добавьте больше навыков в профиль!
            </div>
        `);
        return;
    }

    let html = '<div class="list-group">';

    items.forEach(function(item, index) {
        let delay = index * 100;

        if (type === 'vacancy') {
            html += `
                <a href="/vacancy/${item.id}" class="list-group-item list-group-item-action" style="animation: fadeIn 0.5s ease-out ${delay}ms both;">
                    <div class="d-flex w-100 justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${item.title}</h6>
                            <small class="text-muted">
                                <i class="bi bi-building"></i> ${item.company || ''}
                            </small>
                        </div>
                        <span class="badge bg-primary">${item.salary || ''}</span>
                    </div>
                    <p class="mb-0 mt-2 small">
                        <i class="bi bi-geo-alt"></i> ${item.location || 'Не указано'}
                    </p>
                </a>
            `;
        } else {
            html += `
                <a href="/course/${item.id}" class="list-group-item list-group-item-action" style="animation: fadeIn 0.5s ease-out ${delay}ms both;">
                    <div class="d-flex w-100 justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${item.title}</h6>
                            <small class="text-muted">
                                <i class="bi bi-building"></i> ${item.provider || ''}
                            </small>
                        </div>
                        <div>
                            <span class="badge bg-warning text-dark me-1">★ ${item.rating || '0'}</span>
                            <span class="badge ${item.price === 0 ? 'bg-success' : 'bg-primary'}">
                                ${item.price ? item.price + ' ₽' : 'Бесплатно'}
                            </span>
                        </div>
                    </div>
                </a>
            `;
        }
    });

    html += '</div>';
    $(container).html(html);
}

function analyzeProfile() {
    $('#profile-analysis').html(`
        <div class="text-center py-4">
            <div class="loading-spinner mx-auto mb-3"></div>
            <p class="text-muted">Анализируем ваш профиль...</p>
        </div>
    `);

    $.ajax({
        url: '/api/analyze-profile',
        method: 'GET',
        success: function(data) {
            displayProfileAnalysis(data);
        },
        error: function() {
            $('#profile-analysis').html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Ошибка при анализе профиля
                </div>
            `);
        }
    });
}

function displayProfileAnalysis(data) {
    let container = $('#profile-analysis');

    let skillGapsHtml = '';
    if (data.skill_gaps && data.skill_gaps.length > 0) {
        skillGapsHtml = data.skill_gaps.map(skill =>
            `<span class="skill-tag"><i class="bi bi-plus-circle"></i> ${skill}</span>`
        ).join('');
    } else {
        skillGapsHtml = '<p class="text-muted">У вас нет пробелов в навыках!</p>';
    }

    let careerPathHtml = '';
    if (data.recommended_career_path && data.recommended_career_path.length > 0) {
        careerPathHtml = '<ul class="list-unstyled">' +
            data.recommended_career_path.map(path =>
                `<li><i class="bi bi-arrow-right-circle-fill text-primary me-2"></i>${path}</li>`
            ).join('') +
            '</ul>';
    } else {
        careerPathHtml = '<p class="text-muted">Просматривайте вакансии для получения рекомендаций</p>';
    }

    let html = `
        <div class="profile-stats mb-4">
            <div class="row text-center">
                <div class="col-4">
                    <div class="stat-value">${data.total_skills || 0}</div>
                    <div class="stat-label">Навыков</div>
                </div>
                <div class="col-4">
                    <div class="stat-value">${data.skill_gaps ? data.skill_gaps.length : 0}</div>
                    <div class="stat-label">Нужно изучить</div>
                </div>
                <div class="col-4">
                    <div class="stat-value">${data.experience_years || 0}</div>
                    <div class="stat-label">Лет опыта</div>
                </div>
            </div>
        </div>

        <div class="mb-4">
            <h5><i class="bi bi-star-fill text-warning"></i> Ваши топ-навыки</h5>
            <div>
                ${data.top_skills ? data.top_skills.map(skill =>
                    `<span class="badge bg-primary me-1 mb-1 p-2">${skill}</span>`
                ).join('') : 'Нет навыков'}
            </div>
        </div>

        <div class="mb-4">
            <h5><i class="bi bi-lightbulb-fill text-warning"></i> Рекомендуемые навыки</h5>
            <div>
                ${skillGapsHtml}
            </div>
        </div>

        <div>
            <h5><i class="bi bi-compass-fill text-info"></i> Карьерный путь</h5>
            ${careerPathHtml}
        </div>
    `;

    container.html(html);
}

function setupSmoothScroll() {
    $('.page-link').click(function(e) {
        if (!$(this).parent().hasClass('disabled')) {
            $('html, body').animate({
                scrollTop: $('#results-container').offset().top - 100
            }, 300);
        }
    });
}

function showNotification(message, type = 'info') {
    let icon = 'info-circle';
    let bgClass = 'alert-info';

    if (type === 'success') {
        icon = 'check-circle';
        bgClass = 'alert-success';
    } else if (type === 'warning') {
        icon = 'exclamation-triangle';
        bgClass = 'alert-warning';
    } else if (type === 'danger') {
        icon = 'exclamation-circle';
        bgClass = 'alert-danger';
    }

    let notification = `
        <div class="alert ${bgClass} alert-dismissible fade show" role="alert">
            <i class="bi bi-${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    $('#notification-area').html(notification);

    setTimeout(() => {
        $('.alert').fadeOut('slow');
    }, 5000);
}

function validateForm(formId) {
    let isValid = true;
    $(`#${formId} [required]`).each(function() {
        if (!$(this).val()) {
            $(this).addClass('is-invalid');
            isValid = false;

            $(this).focus(function() {
                $(this).removeClass('is-invalid');
            });
        } else {
            $(this).removeClass('is-invalid');
        }
    });

    if (!isValid) {
        showNotification('Пожалуйста, заполните все обязательные поля', 'warning');
    }

    return isValid;
}

function saveSearch(query, filters) {
    $.ajax({
        url: '/api/save-search',
        method: 'POST',
        data: {
            query: query,
            filters: JSON.stringify(filters)
        },
        success: function() {
            console.log('Поиск сохранен');
        }
    });
}

$(document).keyup(function(e) {
    if (e.key === 'Escape') {
        $('.modal').modal('hide');
    }

    if (e.ctrlKey && e.key === 'Enter') {
        $('form').submit();
    }
});