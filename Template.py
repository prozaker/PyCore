#!/usr/bin/env python

from SubspaceBot import *
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        # register Your Module
        ssbot.registerModuleInfo(
            __name__,
            "Info/LagBot",
            "The Junky",
            "displays/checks players lag",
            ".01"
        )

        # register your commands
        self.cmd_dict = {
            ssbot.registerCommand(
                '!whatthef',  # command
                "!wtf",  # alias can be None if no alias
                0,  # min access level to use this command
                # what types of messages this command will accept
                COMMAND_LIST_PP,
                "w.t.f",  # category this command belongs to
                # what args if any this command accepts use "" if none
                "<name>",
                # short description of the command displayed in help
                "what the f"
            ): self.cmdWTF  # cmdHandler(self, ssbot, event)
        }
        # do any other initialization code here
        # ...

    def handle_events(self, ssbot, event):
        # whatever events your bot needs to respond to add code here to do it
        if event.type == EVENT_LOGIN:
            pass
        elif event.type == EVENT_COMMAND and \
                event.command.id in self.cmd_dict:
            self.cmd_dict[event.command.id](ssbot, event)
        elif event.type == EVENT_TICK:
            timer_expired = self.tm.getExpired()
            if timer_expired:
                # timer_expired is now the data we passed to timer
                if timer_expired.data == 1:
                    pass
        elif event.type == EVENT_DISCONNECT:
            pass

    def cmdWTF(self, ssbot, event):
        ssbot.sendReply(event, "wtf")

    def cleanup(self):
        # put any cleanup code in here this is called when bot is about to die
        pass


if __name__ == '__main__':
    # bot runs in this if not run by master
    # generic main function for when you run bot in standalone mode
    # we pass in the Bot class to the function, so it can run it for us
    bot_main(Bot)
