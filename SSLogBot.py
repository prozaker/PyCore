#!/usr/bin/env python

import time

from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.constants.events import *
from subspace_bot.constants.commands import *
from subspace_bot.constants.messages import *

class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        # register Your Module
        ssbot.register_module_info(
            __name__,
            "subgamelogbot",
            "The Junky",
            "displays onscreen *log",
            ".01"
        )
        # register your commands
        self.cmd_id_log = ssbot.register_command(
            '!sslog',
            "!sl",
            5,
            COMMAND_LIST_PP,
            "smods",
            "",
            "same as *log for nonsysops"
        )

        self.log_player = None
        self.log_time = time.time()

    def handle_events(self, ssbot, event):
        if event.type == EVENT_COMMAND and event.command.id == self.cmd_id_log:
            self.log_player = event.player
            self._log_time = time.time() + 5
            ssbot.send_private_message(event.player, "ok")
            ssbot.send_public_message("*log")
        if (event.type == EVENT_MESSAGE and
                event.message_type == MESSAGE_TYPE_ARENA and
                self.log_player is not None):
            m = event.message
            if m.startswith(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                ssbot.send_private_message(self.log_player, m)
        if (event.type == EVENT_TICK and
                self.log_player is not None and
                self.log_time >= time.time()):
            self.log_player = None
        if (event.type == EVENT_LEAVE and event.player == self.log_player):
            self.log_player = None

    def cleanup(self):
        # put any cleanup code in here this is called when bot is about to die
        pass

if __name__ == '__main__':
    # bot runs in this if not run by master
    # generic main function for when you run bot in standalone mode
    # we pass in the Bot class to the function, so it can run it for us
    bot_main(Bot)
