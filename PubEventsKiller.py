import TimerManager
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.constants.events import *


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        ssbot.register_module_info(
            __name__,
            "pubeventskiller",
            "The Junky",
            "pubeventsk",
            ".01"
        )
        self.botname2kill = "Bot-EG-Pubvents"
        self.answered = True
        self.tm = TimerManager.TimerManager()
        self.tm.set(10, 1)
        self.bots_to_check = {
            "Bot-EG-Pubvents": True,
        }
        pass

    def handle_events(self, ssbot, event):
        if event.type == EVENT_TICK:
            timer_expired = self.tm.getExpired()
            if timer_expired:
                # timer_expired is now the data we passed to timer
                if timer_expired.data == 1:
                            for bname, answered in \
                                    self.killable_bots.iteritems():
                                p = ssbot.find_player_by_name(bname)
                                if p:
                                    if answered:
                                        ssbot.send_private_message(p, "!wtf")
                                        self.bots_to_check[event.pname] = False
                                    else:
                                        ssbot.send_private_message(p, "*kill")
                                        ssbot.send_public_message(
                                            "?alert %s is not responding and"
                                            " has been killed" % bname
                                        )
                                        self.bots_to_check[event.pname] = True
                            self.tm.set(60, 1)
        elif event.type in [EVENT_COMMAND, EVENT_MESSAGE]:
            if event.pname in self.bots_to_check:
                self.bots_to_check[event.pname] = True

    def cleanup(self):
        pass

if __name__ == '__main__':
    bot_main(Bot, False, False, "99")
