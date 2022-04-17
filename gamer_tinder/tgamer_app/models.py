from django.db import models


class Game(models.Model):
    title = models.CharField('Название', max_length=100)
    genre = models.CharField('Жанр', max_length=100, default='')
    description = models.TextField('Описание игры')
    poster = models.ImageField('Постер', upload_to='media/games/')

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class Player(models.Model):
    telegram_id = models.IntegerField('Телеграм айди')
    nickname = models.CharField('Имя', max_length=30, blank=False)
    prefered_game = models.ForeignKey(Game, verbose_name='Любимая игра',
                                      related_name='Игроки',
                                      on_delete=models.SET_NULL,
                                      null=True)
    search_enabled = models.BooleanField('Поиск включен', default=True)

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
