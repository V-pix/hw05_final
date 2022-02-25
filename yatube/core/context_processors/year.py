from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    now = timezone.now()
    now_year = now.year
    return {
        'year': now_year,
    }
