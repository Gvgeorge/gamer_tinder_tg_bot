import telepot
import os
import time
from telepot.loop import MessageLoop
from telepot.helper import DefaultRouterMixin
from telepot.namedtuple import ReplyKeyboardRemove, Message
from .models import Game, Player
from .validators import validate_steam_name
from .markups import reg_markup, games_markup, teammate_markup
from .storage import StateStorage


TOKEN = os.getenv('TG_API_KEY')


class GamerBot(telepot.Bot, DefaultRouterMixin):
    def __init__(self, token, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.text_route = {'/commands': self.on_commands,
                           '/selectGame': self.set_prefered_game,
                           '/change_steam_name': self.reset_steam_name,
                           '/change_about': self.reset_about,
                           '/change_game': self.reset_prefered_game,
                           '/enableSearch': self.set_enable_search,
                           '/disableSearch': self.set_disable_search,
                           '/find': self.find_friends,
                           '/next': self.next_teammate,
                           '/invite': self.invite
                           }
        self._router.routing_table['chat'] = self.text_router
        self.available_commands = '\n'.join(self.text_route.keys())
        self._state = StateStorage()
        self._games = Game.objects.all()

    def text_router(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            return self.sendMessage(
                chat_id, 'Данный бот принимает только текстовые сообщения')
        msg_text = msg['text']
        # наверное можно как-то сделать чтобы не запрашивать бд

        player, player_is_new = Player.objects.get_or_create(pk=chat_id)

        if player_is_new:
            return self.sendMessage(
                player.tg_id,
                'Для того чтобы использовать этот бот ' +
                'нужно зарегистрироваться нажмите на кнопку ниже.',
                reply_markup=reg_markup)

        if player.sign_up != player.RegistrationSteps.DONE:
            return self.register(player, msg_text)

        if self._state.get_search_status(player):
            game = self.parse_game_setting_msg(player, msg['text'])
            self._state.set_current_game(player, game)
            return self.find_friends(player, msg)

        if msg_text.strip() in ['/find', '/invite']:
            return self.text_route[msg_text](player, msg)
        return self.text_route.get(msg_text, self.on_default)(player, msg_text)

    def register(self, player: Player, msg_text: str, start: bool = False):
        if start:
            return self.send_next_registration_message(player)

        if player.sign_up == player.RegistrationSteps.STEAM_NAME:
            # валидаторы бы как-то передать в функцию или класс
            steam_name_is_valid, validator_msg = validate_steam_name(msg_text)
            if not steam_name_is_valid:
                return self.sendMessage(player.tg_id, validator_msg)
            else:
                self.set_steam_name(player, msg_text)

        elif player.sign_up == player.RegistrationSteps.ABOUT:
            self.set_about(player, msg_text)

        elif player.sign_up == player.RegistrationSteps.PREFERED_GAME:
            game = self.parse_game_setting_msg(player, msg_text)
            self.set_prefered_game(player, game)

        return self.send_next_registration_message(player)

    def parse_game_setting_msg(self, player: Player, msg_text: str):
        game_id = int(msg_text.split()[0])
        try:
            game = Game.objects.get(pk=game_id)
            return game

        except Game.DoesNotExist:
            self.sendMessage(
                player.tg_id,
                'выберите пожалуйста игру из списка ниже: ',
                reply_markup=games_markup)
            return None

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
        return self.sendMessage(player.tg_id, msg_text, reply_markup=markup)

    def set_steam_name(self, player: Player, msg_text: str) -> None:
        player.steam_name = msg_text
        player.save(update_fields=['steam_name', 'sign_up'])

    def set_about(self, player: Player, msg_text: str) -> None:
        player.about = msg_text
        player.save(update_fields=['about', 'sign_up'])

    def set_prefered_game(self, player: Player, game: Game):
        player.prefered_game = game
        player.save(update_fields=['prefered_game', 'sign_up'])

    def set_enable_search(self, player: Player, msg) -> None:
        player.search_enabled = True
        player.save(update_fields=['search_enabled'])
        self.sendMessage(player.tg_id, 'Поиск включен.')

    def set_disable_search(self, player: Player, msg) -> None:
        player.search_enabled = False
        player.save(update_fields=['search_enabled'])
        self.sendMessage(player.tg_id, 'Поиск выключен.')

    def on_default(self, player, msg_text):
        self.sendMessage(
            player.tg_id, 'Простите, я вас не понял. Список комманд:' +
            f'\n{self.available_commands}')

    def on_commands(self, player, msg_text):
        self.sendMessage(
            player.tg_id, f'Список комманд: \n{self.available_commands}')

    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        # тут бы стоило его передать?
        # Просто так не передается нужно переделывать функцию из библиотеки
        player = Player.objects.get(pk=from_id)

        msg_text = msg['message']['text']

        if data == 'registration':
            self.register(player, msg_text, start=True)

    def reset_steam_name(self, player, msg):
        player.steam_name = ''
        player.save(update_fields=['steam_name', 'sign_up'])
        return self.register(player, '', start=True)

    def reset_about(self, player, msg):
        player.about = ''
        player.save(update_fields=['about', 'sign_up'])
        return self.register(player, '', start=True)

    def reset_prefered_game(self, player, msg):
        player.prefered_game = None
        player.save(update_fields=['prefered_game', 'sign_up'])
        return self.register(player, '', start=True)

    def check_username_set(self, player: Player, msg: Message):
        try:
            username = msg['from']['username']
        except KeyError:
            return self.sendMessage(
                player.tg_id,
                'Для использования этой комманды нужно в настройках профиля ' +
                'указать username')
        return username

    def find_friends(self, player: Player, msg: Message):
        if not self._state.get_search_status(player):
            self.check_username_set(player, msg)
            self.sendMessage(player.tg_id, 'Выберите игру',
                             reply_markup=games_markup)
            self._state.set_search_status(player, True)
        else:
            self._state.set_search_status(player, False)
            game = self._state.get_current_game(player)

            teammates = self._state.update_possible_teammates(
                player, game)
            if not teammates:
                return self.sendMessage(
                    player.tg_id,
                    'Ни одного игрока, соответствующего вашим предпочтениям' +
                    'не найдено.')
            return self.next_teammate(player, msg)

    def next_teammate(self, player: Player, msg: Message):
        try:
            possible_teammate = self._state.get_next_teammate(player)
        except IndexError:
            return self.sendMessage(
                player.tg_id, 'Других игроков по вашему запросу не найдено.')
        possible_teammate_card = self.prepare_player_card(possible_teammate)
        return self.sendMessage(player.tg_id,
                                possible_teammate_card,
                                reply_markup=teammate_markup)

    def invite(self, player: Player, msg: Message):
        username = self.check_username_set(player, msg)
        teammate = self._state.get_current_teammate(player)
        self.sendMessage(
            teammate.tg_id,
            f'Пользователю {username} понравилась ваша карточка по игре.' +
            ' Напиши ему!')
        return self.sendMessage(
            player.tg_id, 
            f'Сообщение {teammate.steam_name} успешно отправлено!')

    def prepare_player_card(self, player: Player) -> str:
        card = f'Игрок: {player.steam_name}.\n' + \
               f'Любимая игра: {player.prefered_game.title}.\n' + \
               f'Об игроке: {player.about}'
        return card


MessageLoop(GamerBot(TOKEN)).run_as_thread()

while 1:
    time.sleep(10)
