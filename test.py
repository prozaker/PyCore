'''
@author: The Junky
'''

from random import randrange

from BotUtilities import *
from SubspaceBot import *


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        ssbot.registerModuleInfo(
            __name__,
            "Pythonbot-Rota",
            "Fortunae.Rota",
            "Rolls a random int from 1 to 100",
            ".01"
        )

        self.__command_handlers_dict = {
            ssbot.registerCommand(
                '!roll',
                None,
                0,
                COMMAND_LIST_PP,
                "random",
                "",
                "Rolls random positive int up to 100"
            ): self.roll,
        }

    def HandleEvents(self, ssbot, event):
        if event.type == EVENT_COMMAND:
            if event.command.id in self.__command_handlers_dict:
                self.__command_handlers_dict[event.command.id](ssbot, event)

    def roll(self, bot, event):
        random_number = randrange(1, 101)
        bot.sendArenaMessage(
            event.player.name + ' rolled ' + str(random_number) + ' (1-100)')


if __name__ == '__main__':
    botMain(Bot)
