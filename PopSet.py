import TimerManager
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.constants.commands import *
from subspace_bot.constants.ships import *
from subspace_bot.constants.events import *


class Tier():
    def __init__(self, min_pop, sets, desc, next_timer):
        self.min_pop = min_pop
        self.sets = sets
        self.desc = desc
        self.next_timer = next_timer

    def addSettings(self, set):
        self.sets.append(set)

    def isTransitionable(self, pop):
        if pop <= self.min_pop:
            return True
        else:
            return False

    def getId(self):
        return self.min_pop

    def doTransition(self, ssbot, c):
        ssbot.send_change_settings(self.sets)
        ssbot.send_arena_message(
            "Population(%s): settings changed to POPSET: %s" %
            (str(c), self.desc)
        )
        ssbot.send_public_message(
            "*bot Population(%s): settings changed to POPSET: %s" %
            (str(c), self.desc)
        )

    def printReply(self, ssbot, event):
        ssbot.send_reply(
            event,
            "Tier: " + self.desc + " MinPop: " + str(self.min_pop)
        )
        for s in self.sets:
            ssbot.send_reply(event, "Tier Setting(s):" + s)

    def printPublic(self, ssbot):
        ssbot.send_public_message(
            "Tier: " + self.desc + " MinPop: " + str(self.min_pop))
        for s in self.sets:
            ssbot.send_public_message("Tier Setting(s):" + s)

    def __repr__(self):
        return self.desc

    def getNextTimerDelay(self):
        return self.next_timer


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        # register Your Module
        ssbot.register_module_info(
            __name__,
            "Popset",
            "The Junky",
            "Controls settings based on current # of players in ships",
            ".03"
        )
        # register your commands
        self.cmddt = ssbot.register_command(
            '!doTransition',
            "!dt",
            2,
            COMMAND_LIST_PP,
            "Popset",
            "[on|off|normal]",
            "Control settings based on pop"
        )
        self.cmdlt = ssbot.register_command(
            '!listTransition', "!lt",
            0,
            COMMAND_LIST_PP,
            "Popset",
            "",
            "list all transitions/settings"
        )
        self.normal = Tier(
            20,
            ["Team:MaxPerTeam:10", "Team:MaxPerPrivateTeam:10"],
            "Normal",
            15 * 60
        )
        self.tiers = [
            Tier(
                10,
                ["Team:MaxPerTeam:5", "Team:MaxPerPrivateTeam:5"],
                "Small", 3 * 60
            ),
            Tier(
                16,
                ["Team:MaxPerTeam:8", "Team:MaxPerPrivateTeam:8"],
                "Medium",
                10 * 60
            ),
            self.normal
        ]

        self.current = None
        self.tm = TimerManager.TimerManager()
        self.enabled = True

    def doTransition(self, ssbot):
        c = 0
        for p in ssbot.players_here:
            if p.ship != SHIP_NONE:
                c += 1
                # print str(c) + ":" + p.name
        for t in self.tiers:
            # this is the tier we should be on
            if t.isTransitionable(c):
                # only if it is different from current rier do we change
                if self.current is None or self.current.getId() != t.getId():
                    t.doTransition(ssbot, c)
                    self.current = t
                break

    def handle_events(self, ssbot, event):
        if event.type == EVENT_LOGIN:
            # first check 5 secs after login
            self.tm.set(5, 1)
        elif event.type == EVENT_COMMAND:
            if event.command.id == self.cmddt:
                if len(event.arguments) == 1:
                    if event.arguments[0].lower() == "on":
                        if not self.enabled:
                            self.enabled = True
                            self.tm.set(1, 1)
                            ssbot.send_reply(event, "ok")
                    elif event.arguments[0].lower() == "off":
                        if self.enabled:
                            self.enabled = False
                            self.tm.deleteAll()
                            ssbot.send_reply(event, "ok")
                    elif event.arguments[0].lower() == "normal":
                        if self.enabled:
                            self.enabled = False
                            self.tm.deleteAll()
                            self.normal.doTransition(ssbot, event.pname)
                            ssbot.send_reply(event, "ok")
                    else:
                        self.doTransition(ssbot)
            elif event.command.id == self.cmdlt:
                ssbot.send_reply(event, "Current Setting:" + str(self.current))
                for t in self.tiers:
                    t.printReply(ssbot, event)
        elif event.type == EVENT_ENTER:
            if self.current:
                ssbot.send_private_message(
                    event.player,
                    "Current Setting:%s ::!lt for more details" % str(
                        self.current)
                )
        elif event.type == EVENT_TICK:
            timer_expired = self.tm.getExpired()
            if timer_expired:
                # timer_expired is now the data we passed to timer
                if timer_expired.data == 1:
                    self.doTransition(ssbot)
                    # changed by serexl on 12/15, originally
                    # self.tm.set(self.current.getNextTimerDelay(), 1)
                    self.tm.set(5 * 60, 1)

    def cleanup(self):
        # put any cleanup code in here this is called when bot is about to die
        pass

if __name__ == '__main__':
    # bot runs in this if not run by master
    # generic main function for when you run bot in standalone mode
    # we pass in the Bot class to the function, so it can run it for us
    bot_main(Bot, False, False, "#master")
