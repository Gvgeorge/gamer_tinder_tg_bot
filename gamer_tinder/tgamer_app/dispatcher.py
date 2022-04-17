import telepot
import os
from pprint import pprint
from telepot.loop import MessageLoop
import time


token = os.getenv('TG_API_KEY')
tg_bot = telepot.Bot(token)


def handle(msg):
    flavor = telepot.flavor(msg)

    summary = telepot.glance(msg, flavor=flavor)
    pprint([flavor, summary])
    pprint(msg)


MessageLoop(tg_bot, handle).run_as_thread()

while 1:
    time.sleep(10)
