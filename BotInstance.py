# -*- coding: UTF-8 -*-
"""
masterbot for cycad's python core written by The Junky<thejunky@gmail.com>
@author: The Junky
"""
import logging
import time
from threading import Thread

from subspace_bot.objects.bot import SubspaceBot
from subspace_bot.utilities.loggers import log_exception
from subspace_bot.utilities.module import load_bot


class BotInstance(Thread):
    def __init__(self, bot_id, type, description, owner, bname, bpassword,
                 inifile, host, port, arena, modules, MQueue, args, logger):
        Thread.__init__(self)
        self.id = bot_id
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
            self.ssbot.queue_broadcast(event)

    def run(self):
        ssbot = None
        botlist = []
        try:
            ssbot = SubspaceBot(False, False, self.MQueue, logging.getLogger(
                "ML." + self.type + ".Core"))
            ssbot.set_bot_info(self.type, self.description, self.owner)
            self.ssbot = ssbot
            ssbot.arena = self.arena  # serexl's bots look at arena in init
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
                    botlist.append(bot)
            retry = 0
            while self.keepgoing:
                ssbot.connect_to_server(
                    self.host,
                    self.port,
                    self.bname,
                    self.bpassword,
                    self.arena
                )
                while ssbot.is_connected() and self.keepgoing:
                        retry = 0
                        event = ssbot.wait_for_event()
                        for b in botlist:
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
            log_exception(self.logger)
        finally:
            if isinstance(ssbot, SubspaceBot) and ssbot.is_connected():
                ssbot.disconnect_from_server()
            for b in botlist:
                b.cleanup()
