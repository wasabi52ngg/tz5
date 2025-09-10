from django.shortcuts import render
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from django.conf import settings


@main_auth(on_cookies=True)
def index(request):
    """Главная страница приложения"""
    app_settings = settings.APP_SETTINGS
    context = {
        'user': request.bitrix_user,
        'is_authenticated': True,
        'app_settings': app_settings
    }
    return render(request, 'main_app/index.html', context)
