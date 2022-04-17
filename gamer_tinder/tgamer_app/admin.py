from django.contrib import admin
from .models import Game, Player


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    pass


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    pass
