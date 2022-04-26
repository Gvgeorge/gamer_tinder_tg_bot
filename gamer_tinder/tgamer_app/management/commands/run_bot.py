from django.core.management.base import BaseCommand
from tgamer_app.gamer_bot import main


class Command(BaseCommand):
    help = 'Runs the bot!'

    def handle(self, *args, **options):
        main()
