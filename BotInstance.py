# -*- coding: UTF-8 -*-
'''
masterbot for cycad's python core written by The Junky<thejunky@gmail.com>
@author: The Junky
'''

from threading import Thread

from SubspaceBot import *
from BotUtilities import *
from subspace_bot.utilities.logging import LogException
from subspace_bot.utilities.module import load_bot


class BotInstance(Thread):
    def __init__(self, id, type, description, owner, bname, bpassword,
                 inifile, host, port, arena, modules, MQueue, args, logger):
        Thread.__init__(self)
        self.id = id
        self.type = type
        self.description = description
        self.owner = owner
        self.bname = bname
        self.setName(bname)
        self.bpassword = bpassword
        self.inifile = inifile
        self.host = host
        self.port = port
        self.arena = arena
        self.modules = modules
        self.ssbot = None
        self.keepgoing = True
        self.logger = logger
        self.MQueue = MQueue
        self.args = args

    def RequestStop(self):
        self.keepgoing = False
        self.ssbot.reconnect = False
        if self.ssbot is not None:
            self.ssbot.disconnect_from_server()

    def queueBroadcast(self, event):  # used by master
        if self.ssbot:
            self.ssbot.queueBroadcast(event)

    def run(self):
        try:
            BotList = []
            ssbot = SubspaceBot(False, False, self.MQueue, logging.getLogger(
                "ML." + self.type + ".Core"))
            ssbot.setBotInfo(self.type, self.description, self.owner)
            self.ssbot = ssbot
            ssbot.arena = self.arena  # serexl's bots look at arena in init
            bot = None
            for m in self.modules:
                bot = load_bot(
                    ssbot,
                    m[0],
                    m[1],
                    self.inifile,
                    self.args,
                    logging.getLogger("ML." + self.type + "." + m[0])
                )
                if bot:
                    BotList.append(bot)
                bot = None
            retry = 0
            while self.keepgoing:
                ssbot.connect_to_server(
                    self.host,
                    self.port,
                    self.bname,
                    self.bpassword,
                    self.arena
                )
                while ssbot.isConnected() and self.keepgoing:
                        retry = 0
                        event = ssbot.wait_for_event()
                        for b in BotList:
                            b.handle_events(ssbot, event)
                if ssbot.should_reconnect() and retry < 6:
                    self.logger.debug("Disconnected...")
                    ssbot.reset_state()
                    retry += 1
                    time.sleep(60 * retry)
                    self.logger.debug("Reconnecting...")
                else:
                    break

        except:
            LogException(self.logger)
        finally:
            if ssbot.isConnected():
                ssbot.disconnect_from_server()
            for b in BotList:
                b.cleanup()
