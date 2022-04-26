from .models import Game, Player
import random


class StateStorage:
    def __init__(self):
        self._possible_teammates = []
        self._current_teammate = None
        self._current_game = None
        self._search_status = False

    def get_current_teammate(self) -> Player:
        return self._current_teammate

    def get_next_teammate(self) -> Player:
        teammate = self._possible_teammates.pop()
        self._current_teammate = teammate
        return teammate

    def update_possible_teammates(self, player: Player, game: Game) -> list:
        '''
        loads possible teammates from the database
        '''
        self._possible_teammates = list(player.get_possible_teammates(game))
        random.shuffle(self._possible_teammates)
        return self._possible_teammates

    def get_possible_teammates(self) -> list:
        return self._possible_teammates

    def set_current_game(self, game: Game) -> None:
        self._current_game = game

    def get_current_game(self, player: Player) -> Game:
        return self._current_game

    def set_search_status(self, value: bool) -> None:
        self._search_status = value

    def get_search_status(self):
        return self._search_status
