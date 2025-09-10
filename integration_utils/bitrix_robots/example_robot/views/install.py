from django.http import HttpResponse

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from integration_utils.bitrix_robots.example_robot.models import ExampleRobot


@main_auth(on_cookies=True)
def install(request):
    try:
        ExampleRobot.install_or_update('bitrix_robot_example:handler', request.bitrix_user_token)
    except Exception as exc:
        return HttpResponse(str(exc))

    return HttpResponse('ok')
