from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, \
     ReplyKeyboardMarkup, KeyboardButton
from .models import Game


def build_keyboard(buttons: list, per_line: int):
    '''
    Given a list of buttons returns a list of lists
    per_line buttons in each list
    '''
    res = []
    tmp_list = []
    for idx, item in enumerate(buttons):
        tmp_list.append(item)
        if (idx + 1) % per_line == 0:
            res.append(tmp_list)
            tmp_list = []
    if tmp_list:
        res.append(tmp_list)
    return res


# markup for registration start keyboard
reg_button = InlineKeyboardButton(text='registration',
                                  callback_data='registration')
reg_markup = InlineKeyboardMarkup(inline_keyboard=[[reg_button]])

# markup for selecting favourite game keyboard
games = [(game.id, game.title) for game in Game.objects.all()]
games_keyboard = build_keyboard([KeyboardButton(text=f'{game[0]} {game[1]}')
                                for game in games], 3)
games_markup = ReplyKeyboardMarkup(keyboard=games_keyboard)
