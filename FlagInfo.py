"""
@author: The Junky
"""


from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.utilities.graphics import tiles_to_ss_coords, \
    tiles_to_ss_area
from subspace_bot.constants.commands import *
from subspace_bot.constants.messages import *
from subspace_bot.constants.events import *
from subspace_bot.constants.ships import *
from subspace_bot.constants.other import COORD_NONE


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        # register Your Module
        ssbot.register_module_info(
            __name__,
            "Flaginfo",
            "The Junky",
            "allows mods to neut specific flags",
            ".01"
        )
        # register your commands
        self.cmd_dict = {
            # ssbot.register_command(
            #   # command
            #   # alias can be None if no alias
            #   # min access level to use this command
            #   # what types of messages this command will accept
            #   # category this command belongs to
            #   # what args if any this command accepts use "" if none
            #   # short description of the command displayed in help
            # ) : # cmdHandler(self, ssbot, event)
            ssbot.register_command(
                '!listflags',
                "!lf",
                1,
                COMMAND_LIST_PP,
                "Flag",
                "",
                "List all flags in the arena"): self.cmdLF,

            ssbot.register_command(
                '!pickupflags',
                "!pf",
                1,
                COMMAND_LIST_PP,
                "Flag",
                "fid1, fid2...",
                "pickup flags by id"): self.cmdPF,

            ssbot.register_command(
                '!warpto',
                "!wt",
                1,
                COMMAND_LIST_PP,
                "Mod",
                "SScoord",
                "e.g A1 or T20 use -!+ for low, mid, high"): self.cmdWT,

            ssbot.register_command(
                '!flagwarpto',
                "!fwt",
                1,
                COMMAND_LIST_PP,
                "Mod",
                "flag_id",
                "warpto the coords of a flag"): self.cmdFWT
        }
        # do any other initialization code here
        # ...
        self.maxflags = 30
        self.pstate = 0
        self.flist = []
        self.fc = 0

    def handle_events(self, ssbot, event):
        # whatever events your bot needs to respond to add code here to do it
        if event.type == EVENT_LOGIN:
            ssbot.send_public_message("?get flag:maxflags")
        elif event.type == EVENT_COMMAND and event.command.id in \
                self.cmd_dict:
            self.cmd_dict[event.command.id](ssbot, event)
        elif event.type == EVENT_MESSAGE and event.message_type == \
                MESSAGE_TYPE_ARENA:
            if event.message.startswith("flag:maxflags="):
                self.maxflags = int(event.message[len("flag:maxflags="):])
        elif event.type == EVENT_CHANGE:
            p = event.player
            if p.pid == ssbot.pid:
                if p.ship == SHIP_WARBIRD:
                    if self.pstate == 1:
                        ssbot.send_freq_change(9998)
                        self.pstate = 2
                    elif self.pstate == 2:
                        for f in self.flist:
                            ssbot.send_pickup_flags(f)
                if p.ship == SHIP_JAVELIN and self.pstate == 3:
                        ssbot.send_ship_change(SHIP_NONE)
                        ssbot.send_public_message("*arenaFlags neuted")
                        self.pstate = 4
        elif event.type == EVENT_FLAG_PICKUP:
            p = event.player
            if p.pid == ssbot.pid:
                self.fc += 1
                if self.fc == len(self.flist):
                    ssbot.send_ship_change(SHIP_JAVELIN)
                    self.pstate = 3

    def cmdLF(self, ssbot, event):
        for p in ssbot.players_here:
            if p.flag_count > 0:
                ssbot.send_reply(event, "Carried: %s:(%d) flags" % (
                    p.name, p.flag_count))
        for i in range(self.maxflags):
            f = ssbot.flag_list[i]
            if f.x != 0xFFFF:
                ssbot.send_reply(event, "(%d:%d, %d)-%s-%s owned by freq:%d" % (
                    f.id, f.x, f.y,
                    tiles_to_ss_coords(f.x, f.y),
                    tiles_to_ss_area(f.x, f.y),
                    f.freq))
        ssbot.send_public_message("?alert %s used !listflags" % (
            event.player.name))

    def cmdPF(self, ssbot, event):
        if len(event.arguments) >= 1:
            if event.arguments[0][0] == '*':
                self.flist = [i for i in range(self.maxflags)
                              if ssbot.flag_list[i].x != 0xFFFF]
            else:
                t = [int(f) for f in event.arguments_after[0].split(", ")]
                self.flist = [i for i in t if ssbot.flag_list[i].x != 0xFFFF]
            self.pstate = 1
            ssbot.send_ship_change(SHIP_WARBIRD)
            ssbot.send_reply(event, "ok")
            ssbot.send_public_message("?alert %s used !pickupflags %s" % (
                event.player.name, event.arguments_after[0]))
        else:
            ssbot.send_reply(event, "no")

    def cmdFWT(self, ssbot, event):
        if len(event.arguments) > 0:
            try:
                fid = int(event.arguments[0])
            except:
                fid = -1
            if fid >= 0 and fid < self.maxflags:
                f = ssbot.flag_list[fid]
                if f.x != COORD_NONE:
                    ssbot.send_reply(event, "*warpto %d %d" % (f.x, f.y))
                    ssbot.send_reply(event, "*bot %s used flagwarpto %d %d" % (
                        event.player.name, f.x, f.y))
                else:
                    ssbot.send_reply(event, "unknown coords or flag carried")
            else:
                ssbot.send_reply(event, "invalid flag id")
        else:
            ssbot.send_reply(event, "invalid syntax !fwt flag_id")

    def cmdWT(self, ssbot, event):
        if len(event.arguments) > 0:
            #   A12 Center of A12
            #   A12-- Top Left of A12
            #   A12-+ TOPleFT
            #   a12!+ mIDDLE lEFT
            s = event.arguments[0].lower()
            c = s[0]
            if c >= 'a' and c <= 't':
                c = ord(c) - ord('a')
                if s[1].isdigit():
                    if len(s) > 2 and s[2].isdigit():
                        n = int(s[1:3])
                        offset = 3
                    else:
                        n = int(s[1:2])
                        offset = 2
                    n -= 1
                    if len(s) == (offset + 2):
                        x = self.computeCoord(c, s[offset])
                        y = self.computeCoord(n, s[offset+1])
                    else:
                        x = self.computeCoord(c, "!")
                        y = self.computeCoord(n, "!")
                    ssbot.send_reply(event, "*bot warpto %d %d" % (
                        event.player.name, x, y))
                    ssbot.send_reply(event, "*warpto %d %d" % (x, y))
                else:
                    ssbot.send_reply(
                        event,
                        "e1:Improper Format use !warpto A1 A12 A12[+-!]"
                    )
            else:
                    ssbot.send_reply(
                        event,
                        "e2:Improper Format use !warpto A1 A12 A12[+-!]"
                    )

    @staticmethod
    def computeCoord(p, po):
        """
        p = 0-20
        po =
            - for lowerbound
            ! for middle
            + for upperbound
        """
        if po == '-':
            return (p*51)+5
        if po == '!':
            return (p*51)+25
        if po == '+':
            return (p*51)+45

    @staticmethod
    def cmdGO(ssbot, event):
        ssbot.send_change_arena(event.arguments[0] if
                              len(event.arguments) > 0 else "99")

    def cleanup(self):
        # put any cleanup code in here this is called when bot is about to die
        pass


if __name__ == '__main__':
    # bot runs in this if not run by master
    # generic main function for when you run bot in standalone mode
    # we pass in the Bot class to the function, so it can run it for us
    bot_main(Bot, False, True, "0")
