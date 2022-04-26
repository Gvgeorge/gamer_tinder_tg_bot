import telepot
import os
import time
from loguru import logger
from django.conf import settings
from telepot.loop import MessageLoop
from telepot.helper import ChatHandler
from telepot.namedtuple import ReplyKeyboardRemove, Message
from telepot.delegate import per_chat_id, create_open, pave_event_space
from .models import Game, Player
from .validators import validate_steam_name
from .markups import reg_markup, games_markup, teammate_markup
from .storage import StateStorage
from . import msgs


TOKEN = settings.TELEGRAM_TOKEN


class GamerBot(ChatHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_route = {'/commands': self.on_commands,
                           '/selectGame': self.set_prefered_game,
                           '/change_steam_name': self.reset_steam_name,
                           '/change_about': self.reset_about,
                           '/change_game': self.reset_prefered_game,
                           '/enableSearch': self.set_enable_search,
                           '/disableSearch': self.set_disable_search,
                           '/find': self.find_friends,
                           '/next': self.next_teammate,
                           '/invite': self.invite,
                           '/help': self.on_commands
                           }
        self._router.routing_table['chat'] = self.text_router
        self.available_commands = '\n'.join(self.text_route.keys())
        self._state = StateStorage()

    def text_router(self, msg):
        '''
        Главный роутер.
        '''
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            return self.sender.sendMessage(msgs.ACCEPTS_MESSAGES_ONLY)
        msg_text = msg['text']

        try:
            player = Player.objects.get(tg_id=chat_id)
        except Player.DoesNotExist:
            if msg_text == '/registration':
                player = Player(tg_id=chat_id)
                player.save()
                return self.register(player, msg_text, start=True)
            else:
                return self.sender.sendMessage(
                    msgs.PLEASE_REGISTER, reply_markup=reg_markup)

        if player.sign_up != player.RegistrationSteps.DONE:
            return self.register(player, msg_text)

        if self._state.get_search_status():
            game = self.parse_game_setting_msg(player, msg['text'])
            self._state.set_current_game(game)
            return self.find_friends(player, msg)

        if msg_text.strip() in ['/find', '/invite']:
            return self.text_route[msg_text](player, msg)
        return self.text_route.get(msg_text, self.on_default)(player, msg_text)

    def register(self, player: Player, msg_text: str, start: bool = False):
        '''
        Дополнительный роутер для процесса регистрации
        '''
        if start:
            return self.send_next_registration_message(player)

        if player.sign_up == player.RegistrationSteps.STEAM_NAME:
            steam_name_is_valid, validator_msg = validate_steam_name(msg_text)
            if not steam_name_is_valid:
                return self.sender.sendMessage(validator_msg)
            else:
                self.set_steam_name(player, msg_text)

        elif player.sign_up == player.RegistrationSteps.ABOUT:
            self.set_about(player, msg_text)

        elif player.sign_up == player.RegistrationSteps.PREFERED_GAME:
            game = self.parse_game_setting_msg(player, msg_text)
            self.set_prefered_game(player, game)

        return self.send_next_registration_message(player)

    def parse_game_setting_msg(self, player: Player, msg_text: str):
        '''Сопоставляет объекты из БД с коммандой выбора игры'''
        try:
            game_id = int(msg_text.split()[0])
            game = Game.objects.get(pk=game_id)
            return game

        except (Game.DoesNotExist, ValueError):
            logger.exception('Error while parcing game name', backtrace=False)
            return None

    def send_next_registration_message(self, player: Player) -> str:
        '''Еще один роутер для шагов связанных с регистрацией'''
        route = {
         player.RegistrationSteps.STEAM_NAME: (msgs.ENTER_STEAM_NAME,
                                               ReplyKeyboardRemove()),
         player.RegistrationSteps.ABOUT: (msgs.ENTER_ABOUT, None),
         player.RegistrationSteps.PREFERED_GAME: (msgs.ENTER_PREF_GAME,
                                                  games_markup),
         player.RegistrationSteps.DONE: (msgs.REG_SUCCESS,
                                         ReplyKeyboardRemove())
         }
        msg_text = route[player.sign_up][0]
        markup = route[player.sign_up][1]
        return self.sender.sendMessage(msg_text, reply_markup=markup)

    def set_steam_name(self, player: Player, msg_text: str) -> None:
        '''Сохраняет информацию об имени в стиме в БД'''
        player.steam_name = msg_text
        player.save(update_fields=['steam_name', 'sign_up'])

    def set_about(self, player: Player, msg_text: str) -> None:
        '''
        Сохраняет информацию об игроке в БД
        '''
        player.about = msg_text
        player.save(update_fields=['about', 'sign_up'])

    def set_prefered_game(self, player: Player, game: Game):
        '''
        Сохраняет любимую игру в бд
        '''
        player.prefered_game = game
        player.save(update_fields=['prefered_game', 'sign_up'])

    def set_enable_search(self, player: Player, msg) -> None:
        '''Включает поиск'''
        player.search_enabled = True
        player.save(update_fields=['search_enabled'])
        self.sender.sendMessage(msgs.SEARCH_ENABLED)

    def set_disable_search(self, player: Player, msg) -> None:
        '''Выключает поиск'''
        player.search_enabled = False
        player.save(update_fields=['search_enabled'])
        self.sender.sendMessage(msgs.SEARCH_DISABLED)

    def on_default(self, player, msg_text):
        '''Хендлер для сообщений которые не предусмотрены ботом'''
        self.sender.sendMessage(
            msgs.NOT_UNDERSTAND +
            f'\n{self.available_commands}')

    def on_commands(self, player, msg_text):
        '''Хендлер для /commands'''
        self.sender.sendMessage(
             f'{msgs.COMMAND_LIST}\n{self.available_commands}')

    def reset_steam_name(self, player, msg):
        '''
        Сбрасывает, поле с именем в стиме, после чего бот автоматически
        попросит пользователя указать любимую игру заново.
        '''
        player.steam_name = ''
        player.save(update_fields=['steam_name', 'sign_up'])
        return self.register(player, '', start=True)

    def reset_about(self, player, msg):
        '''
        Сбрасывает, поле с описанием игрока, после чего бот автоматически
        попросит пользователя указать его заново.
        '''
        player.about = ''
        player.save(update_fields=['about', 'sign_up'])
        return self.register(player, '', start=True)

    def reset_prefered_game(self, player, msg):
        '''
        Сбрасывает, поле с любимой игрой, после чего бот автоматически
        попросит пользователя указать любимую игру заново.
        '''
        player.prefered_game = None
        player.save(update_fields=['prefered_game', 'sign_up'])
        return self.register(player, '', start=True)

    def check_username_set(self, player: Player, msg: Message):
        '''
        Проверка на то установлен ли параметр username у пользователя
        '''
        try:
            username = msg['from']['username']
        except KeyError:
            return self.sender.sendMessage(msgs.SHOW_USERNAME)
        return username

    def find_friends(self, player: Player, msg: Message):
        '''
        Хендл для поиска игрока.
        В if-else сохраняется статус поиска, чтобы роутер вернул нас
        в эту функцию.
        '''
        if not self._state.get_search_status():
            self.check_username_set(player, msg)
            self.sender.sendMessage(
                msgs.ENTER_GAME, reply_markup=games_markup)
            self._state.set_search_status(True)
        else:
            self._state.set_search_status(False)
            game = self._state.get_current_game(player)
            if game is None:
                return self.find_friends(player, msg)
            teammates = self._state.update_possible_teammates(
                player, game)
            if not teammates:
                return self.sender.sendMessage(msgs.NO_PLAYERS_FOUND)
            return self.next_teammate(player, msg)

    def next_teammate(self, player: Player, msg: Message):
        '''Хендл для кнопки некст в поиске'''
        try:
            possible_teammate = self._state.get_next_teammate()
        except IndexError:
            return self.sender.sendMessage(msgs.NO_MORE_PLAYERS_FOUND)
        possible_teammate_card = self.prepare_player_card(possible_teammate)
        return self.sender.sendMessage(
            possible_teammate_card, reply_markup=teammate_markup)

    def invite(self, player: Player, msg: Message):
        '''Хендл для инвайта'''
        username = self.check_username_set(player, msg)
        teammate = self._state.get_current_teammate()
        self.bot.sendMessage(
            teammate.tg_id,
            f'Пользователю {username} понравилась ваша карточка по игре.' +
            ' Напиши ему!')
        return self.sender.sendMessage(
            f'Сообщение {teammate.steam_name} успешно отправлено!')

    def prepare_player_card(self, player: Player) -> str:
        '''Создает карточку игрока, просто строка с информацией'''
        card = f'Игрок: {player.steam_name}.\n' + \
               f'Любимая игра: {player.prefered_game.title}.\n' + \
               f'Об игроке: {player.about}'
        return card

    def on__idle(self, event):
        '''
        Очищаем стейт, чтобы не засорять память.
        '''
        self.close()


# @logger.catch
# def main():
#     bot = telepot.DelegatorBot(TOKEN, [pave_event_space()(
#         per_chat_id(), create_open, GamerBot, timeout=1200),
#     ])
#     MessageLoop(bot).run_as_thread()
#     print('Listening ...')

#     while True:
#         time.sleep(10)


@logger.catch
def main():
    bot = telepot.DelegatorBot(TOKEN, [pave_event_space()(
        per_chat_id(), create_open, GamerBot, timeout=1200),
    ])
    bot.setWebhook(f'https://authdemka.ru/bot/{token}/')

    MessageLoop(bot).run_as_thread()
    print('Listening ...')

    while True:
        time.sleep(10)

import telepot
bot_token = 'BOT_TOKEN'
bot = telepot.Bot(bot_token)
