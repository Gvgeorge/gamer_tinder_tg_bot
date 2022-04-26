from .models import Game, Player
import random


class StateStorage:
    def __init__(self):
        self._possible_teammates = {}
        self._current_teammates = {}
        self._current_games = {}
        self._search_statuses = {}

    def get_current_teammate(self, player: Player) -> Player:
        return self._current_teammates[player]

    def get_next_teammate(self, player: Player) -> Player:
        teammate = self._possible_teammates[player].pop()
        self._current_teammates[player] = teammate
        return teammate

    def update_possible_teammates(self, player: Player, game: Game) -> list:
        '''
        loads possible teammates from the database
        '''
        possible_teammates = list(player.get_possible_teammates(game))
        random.shuffle(possible_teammates)
        self._possible_teammates[player] = possible_teammates
        return possible_teammates

    def get_possible_teammates(self, player: Player) -> list:
        return self._possible_teammates[player]

    def set_current_game(self, player: Player, game: Game) -> None:
        self._current_games[player] = game

    def get_current_game(self, player: Player) -> Game:
        try:
            return self._current_games[player]
        except KeyError:
            return None

    def set_search_status(self, player: Player, value: bool) -> None:
        self._search_statuses[player] = value

    def get_search_status(self, player: Player):
        try:
            return self._search_statuses[player]
        except KeyError:
            return False
