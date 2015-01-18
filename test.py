"""
@author: The Junky
"""

from random import randrange

from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.constants.commands import *
from subspace_bot.constants.events import *

class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        ssbot.register_module_info(
            __name__,
            "Pythonbot-Rota",
            "Fortunae.Rota",
            "Rolls a random int from 1 to 100",
            ".01"
        )

        self.__command_handlers_dict = {
            ssbot.register_command(
                '!roll',
                None,
                0,
                COMMAND_LIST_PP,
                "random",
                "",
                "Rolls random positive int up to 100"
            ): self.roll,
        }

    def handle_events(self, ssbot, event):
        if event.type == EVENT_COMMAND:
            if event.command.id in self.__command_handlers_dict:
                self.__command_handlers_dict[event.command.id](ssbot, event)

    def roll(self, bot, event):
        random_number = randrange(1, 101)
        bot.send_arena_message(
            event.player.name + ' rolled ' + str(random_number) + ' (1-100)')


if __name__ == '__main__':
    bot_main(Bot)
