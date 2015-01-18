#!/usr/bin/env python
"""
@author: The Junky <thejunky@gmail.com>
---
Subgame Peering Assistant
---
This module will just add Arenas sent by powerball's
new peering module to server.ini peering section
dynamically, so when players in subgame zones ?go PB:0
or ?go to anyother peered arena it will work.

"""

import TimerManager
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.constants.events import *


class Bot(BotInterface):
    def __init__(self, ssbot, md):
        BotInterface.__init__(self, ssbot, md)
        # register Your Module
        ssbot.register_module_info(
            __name__,
            "SG Peering Assistant",
            "The Junky",
            "adds peered arenas to ini dynamically",
            ".01"
        )
        # "CZ":[4, set()] the 4 means it will go into [peer4] section
        self.zones = {
            "TW": [0, set(), ["", "0"]],
            "SWZ": [1, set(), ["", "0"]],
            "CZ": [2, set(), ["", "0"]],
            "DSB": [3, set(), ["", "0", ]],
            "PB": [4, set(), ["", "0", "replay"]],
            "EG2": [5, set(), ["", "0", "egfl"]],
            "TS": [6, set(), ["", "0"]]
        }
        self.peers = {
            # peerid:(old, new)
            0: [set(), set()],
            1: [set(), set()],
            2: [set(), set()],
            3: [set(), set()],
            4: [set(), set()],
            5: [set(), set()],
            6: [set(), set()]
        }
        self.timer_man = TimerManager.TimerManager()
        self.timer_man.set(20, 1)

    def handle_events(self, ssbot, event):
        # whatever events your bot needs to respond to add code here to do it
        if event.type == EVENT_LOGIN:
            ssbot.send_public_message("?Arena")

        elif event.type == EVENT_TICK:
            timer_expired = self.timer_man.getExpired()  # a timer expired
            if timer_expired:
                # self.logger.info("timer expired")
                if timer_expired.data == 1:
                    # self.logger.info("?arena")
                    ssbot.send_public_message("?Arena")
                    self.timer_man.set(20, 1)

        elif event.type == EVENT_ARENA_LIST:
            for k, v in self.zones.iteritems():
                v[1].clear()  # clear the set
                v[1].update(v[2])  # add zone default arenas

            for arena in event.arena_list:
                a = arena[0]
                col = a.find(":")
                if col != -1:
                    zone_prefix = a[0:col]
                    arena_name = a[col + 1:].lower()
                    # print "zone: " + zone_prefix + " Arena " + arena_name
                    z = self.zones.get(zone_prefix, None)
                    if z:
                        z[1].add(arena_name)

            for k, v in self.zones.iteritems():
                p = self.peers.get(v[0])
                if p:  # if zone has a peer defined
                    for arena in v[1]:
                        p[1].add(k+arena)  # add the final string to set

            # check if peers lists has changed and send to ss if has
            for k, v in self.peers.iteritems():
                diff = v[0].symmetric_difference(v[1])
                # self.logger.info(v[0])
                # self.logger.info(v[1])
                # self.logger.info(diff)
                if len(diff) > 0:  # wtf list needs to be sent again
                    v[0].clear()
                    v[0] = v[1].copy()
                    s = "*s*peer" + str(k) + ":arenas:"
                    for a in v[0]:
                        s += a + ", "
                    # print s
                    if len(s) > 256:
                        self.logger.debug(
                            "peer" + str(k) + " string too big::" + s)
                        ssbot.send_public_message(s[0:255])
                    else:
                        ssbot.send_public_message(s)
                    # self.logger.info(s)
                # else:
                #    self.logger.info("no change in arenas")

                v[1].clear()  # set new list to Non

    def cleanup(self):
        # put any cleanup code in here this is called when bot is about to die
        pass


if __name__ == '__main__':
    bot_main(Bot)
