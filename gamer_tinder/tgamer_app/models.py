from django.db import models
from django.conf import settings


class Game(models.Model):
    title = models.CharField('Название', max_length=100)
    genre = models.CharField('Жанр', max_length=100, default='')
    description = models.TextField('Описание игры')
    poster = models.ImageField('Постер', upload_to='games/')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class Player(models.Model):
    class RegistrationSteps(models.IntegerChoices):
        '''Сохраняю состояние процесса регистрации'''
        NEW_PLAYER = 0
        STEAM_NAME = 1
        ABOUT = 2
        PREFERED_GAME = 3
        DONE = 4

    tg_id = models.IntegerField('Телеграм айди', primary_key=True)
    steam_name = models.CharField('Имя в стиме',
                                  max_length=settings.STEAM_NAME_MAX_LEN)
    about = models.CharField(verbose_name='О себе',
                             max_length=4096)
    prefered_game = models.ForeignKey(Game, verbose_name='Любимая игра',
                                      related_name='Игроки',
                                      on_delete=models.SET_NULL,
                                      null=True)
    search_enabled = models.BooleanField('Поиск включен', default=True)
    sign_up = models.IntegerField(choices=RegistrationSteps.choices,
                                  default=RegistrationSteps.NEW_PLAYER)

    def update_sign_up_status(self):
        '''
        Функция вычисляет на каком этапе регистрации мы находимся
        '''
        fields_enum = enumerate(
            (self.steam_name, self.about, self.prefered_game), start=1)
        su_status = None
        for idx, field in fields_enum:
            if field is None or not field:
                su_status = self.RegistrationSteps(idx)
                break
        if su_status is None:
            su_status = self.RegistrationSteps.DONE
        self.sign_up = su_status

    def get_possible_teammates(self, game: Game):
        '''
        returns a query of players with search enabled and
        same prefered game
        '''
        qs = Player.objects.filter(search_enabled=True).filter(
            prefered_game=game).exclude(pk=self.tg_id)
        return qs

    def save(self, *args, **kwargs):
        self.update_sign_up_status()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
