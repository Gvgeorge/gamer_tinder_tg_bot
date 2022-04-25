from cgitb import reset
import telepot
import os
from urllib3.exceptions import NewConnectionError
from django.db import Error as DBError
from telepot.loop import MessageLoop
from telepot.helper import DefaultRouterMixin
from telepot.namedtuple import ReplyKeyboardRemove
from .models import Game, Player
from .validators import validate_steam_name
from .markups import reg_markup, games_markup
import time


TOKEN = os.getenv('TG_API_KEY')
# tg_bot = telepot.Bot(token)


class GamerBot(telepot.Bot, DefaultRouterMixin):
    def __init__(self, token, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.text_route = {'/enableSearch': self.set_enable_search,
                           '/disableSearch': self.set_disable_search,
                           '/selectGame': self.set_prefered_game,
                           '/register': self.register,
                           '/change_steam_name': self.reset_steam_name
                           }
        self._router.routing_table['chat'] = self.text_router
        self.available_commands = '\n'.join(self.text_route.keys())
        self._games = Game.objects.all()

    def text_router(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            return self.sendMessage(
                chat_id, 'Данный бот принимает только текстовые сообщения')
        msg_text = msg['text']

        player, player_is_new = Player.objects.get_or_create(pk=chat_id)  # наверное можно как-то сделать чтобы не запрашивать бд

        if player_is_new:
            return self.sendMessage(
                player.tg_id,
                'Для того чтобы использовать этот бот ' +
                'нужно зарегистрироваться нажмите на кнопку ниже.',
                reply_markup=reg_markup)

        if player.sign_up != player.RegistrationSteps.DONE:
            return self.register(player, msg_text)
        return self.text_route.get(msg_text, self.on_default)(player, msg_text)

    def register(self, player: Player, msg_text: str, start: bool=False) -> None:
        if start:
            return self.sendMessage(
                player.tg_id, 'Введите, пожалуйста, свой ник в стиме')

        if player.sign_up == player.RegistrationSteps.STEAM_NAME:
            # валидаторы бы как-то передать в функцию или класс
            steam_name_is_valid, validator_msg = validate_steam_name(msg_text)
            if not steam_name_is_valid:
                return self.sendMessage(player.tg_id, validator_msg)
            else:
                self.set_steam_name(player, msg_text)
                return self.sendMessage(player.tg_id, 'Расскажите о себе.')

        if player.sign_up == player.RegistrationSteps.ABOUT:
            self.set_about(player, msg_text)
            return self.sendMessage(
                player.tg_id, 'Спасибо, теперь, пожалуйста, ' +
                'выберите любимую игру из списка ниже: ',
                reply_markup=games_markup)

        if player.sign_up == player.RegistrationSteps.PREFERED_GAME:
            game_id = int(msg_text.split()[0])
            try:
                game = Game.objects.get(pk=game_id)
                self.set_prefered_game(player, game)
                self.sendMessage(
                    player.tg_id, 'Регистрация успешно завершена!',
                    reply_markup=ReplyKeyboardRemove())

            except Game.DoesNotExist:
                self.sendMessage(
                    player.tg_id,
                    'выберите пожалуйста игру из списка ниже: ',
                    reply_markup=games_markup)

    def send_next_registration_message(self, player: Player) -> str:
        route = {
         player.RegistrationSteps.STEAM_NAME: (
             'Введите, пожалуйста, свой ник в стиме', None),
         player.RegistrationSteps.ABOUT: ('Расскажите о себе.', None),
         player.RegistrationSteps.PREFERED_GAME: (
             'Спасибо, теперь, пожалуйста, ' +
             'выберите любимую игру из списка ниже: ', games_markup),
         player.RegistrationSteps.DONE: (
             'Регистрация успешно завершена!', ReplyKeyboardRemove())}
        msg_text = route[player.sign_up][0]
        markup = route[player.sign_up][1]
        return self.sendMessage(player.id, msg_text, reply_markup=markup)
    
    def set_steam_name(self, player: Player, msg_text: str) -> None:
        player.steam_name = msg_text
        player.save(update_fields=['steam_name', 'sign_up'])

    def set_about(self, player: Player, msg_text: str) -> None:
        player.about = msg_text
        player.save(update_fields=['about', 'sign_up'])

    def set_prefered_game(self, player: Player, game: Game):
        player.prefered_game = game
        player.save(update_fields=['prefered_game', 'sign_up'])

    def select_prefered_game(self, msg, chat_id):
        self.sendMessage(chat_id,
                         'Please select your favourite game below',
                         reply_markup=markup)

    def set_enable_search(self, player: Player, msg) -> None:
        try:
            player.search_enabled = True
            player.save(update_fields=['search_enabled'])
        except NewConnectionError:
            pass  # add to logs
        except DBError:
            self.sendMessage(player.id, 'Что-то пошло не так')

    def set_disable_search(self, player: Player, msg) -> None:
        try:
            player.search_enabled = False
            player.save(update_fields=['search_enabled'])
        except NewConnectionError:
            pass  # add to logs
        except DBError:
            self.sendMessage(player.id, 'Что-то пошло не так')

    def on_default(self, player, msg_text):
        self.sendMessage(player.tg_id, 'Простите, я вас не понял. Список комманд:' +
                         f'\n {self.available_commands}')

    def on_commands(self, player, msg_text):
        self.sendMessage(
            player.tg_id, f'Список комманд: \n {self.available_commands}')

    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        player = Player.objects.get(pk=from_id) # тут бы стоило его передать? Просто так не передается нужно переделывать функцию из библиотеки

        msg_text = msg['message']['text']

        if data == 'registration':
            self.register(player, msg_text, start=True)
        elif data == 'game_selected':
            print('Game selected:', msg)

    def reset_steam_name(self, player, msg):
        player.steam_name = ''
        player.save(update_fields=['steam_name', 'sign_up'])
        return self.register(player, '', start=True)

    def on_inline_query(self, msg):
        pass

    def on_chosen_inline_result(self, msg):
        pass


MessageLoop(GamerBot(TOKEN)).run_as_thread()

while 1:
    time.sleep(10)
