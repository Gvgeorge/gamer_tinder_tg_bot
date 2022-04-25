from django.contrib import admin
from django.utils.html import format_html
from .models import Game, Player


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('image_tag', 'title')

    def image_tag(self, obj):
        return format_html(f'<img src="{obj.poster.url}" style="width:' +
                           '140; height:190px;" />')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    pass
