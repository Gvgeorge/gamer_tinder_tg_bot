from django.core.management.base import BaseCommand
from tgamer_app.gamer_bot import run_as_polling


class Command(BaseCommand):
    help = 'Runs the bot!'

    def handle(self, *args, **options):
        run_as_polling()
