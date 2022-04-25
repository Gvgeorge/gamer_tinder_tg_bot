from .models import Player
from django.conf import settings


def validate_steam_name(
    steam_name: str,
    name_len: int = settings.STEAM_NAME_MAX_LEN
) -> tuple[bool, str]:

    if not steam_name:
        return (False, 'Ник не может быть пустым!')
    if len(steam_name) > name_len:
        return (False, f'Длина ника не может превышать {name_len} символа!')
    return True, 'OK'
