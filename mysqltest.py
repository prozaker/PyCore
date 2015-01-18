"""
@author: The Junky

"""


import TimerManager
from Amysql import *
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.utilities.loggers import LoggingRemoteHandler
from subspace_bot.constants.commands import *
from subspace_bot.constants.events import *
from subspace_bot.constants.messages import *


class Bot(BotInterface):
    def __init__(self, bot, md):
        BotInterface.__init__(self, bot, md)
        bot.register_module_info(
            __name__,
            "MysqLtest",
            "The Junky",
            "mysqlclient for ss",
            ".01"
        )
        self._db = Amysql(self.logger)
        self._db.setDbCredentialsFromFile(self.module_path + R"/db.conf", "db")
        # self._db.setDbCredentialsFromFile(
        #   self.module_path + R"/egnetdb.conf", "db")
        self._db.start()
        self.clist = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_TEAM,
                      COMMAND_TYPE_FREQ, COMMAND_TYPE_PRIVATE,
                      COMMAND_TYPE_CHAT]
        self._sql_command_id = bot.register_command(
            '!sql',
            None,
            9,
            self.clist,
            "web",
            "[query]",
            'sql it zz'
        )
        self._sqlnl_command_id = bot.register_command(
            '!sqlnl',
            None,
            9,
            self.clist,
            "web",
            "[query]",
            'sql it zz'
        )
        self.level = logging.DEBUG
        self.timer_man = TimerManager.TimerManager()
        self.timer_man.set(.01, 1)
        self.timer_man.set(300, 2)
        self.chat = bot.add_chat("st4ff")

        formatter = logging.Formatter('%(message)s')
        handler = LoggingRemoteHandler(logging.DEBUG, bot, "Ratio")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def getMessageTuple(self, event):
        """
            this data will be used later in pretty printer
            when the result is to be printed back to ss
        """
        if event.command_type == MESSAGE_TYPE_PRIVATE:
            target = event.pname
            mtype = event.command_type
        elif event.command_type == MESSAGE_TYPE_REMOTE:
            target = event.pname
            mtype = MESSAGE_TYPE_PRIVATE
        elif event.command_type == MESSAGE_TYPE_FREQ:
            target = event.player.freq
            mtype = event.command_type
        elif event.command_type == MESSAGE_TYPE_CHAT:
            target = event.chat_no
            mtype = event.command_type
        else:
            target = None
            mtype = event.command_type

        return (mtype, target)

    def handle_events(self, ssbot, event):

        if event.type == EVENT_COMMAND:
            ssbot.send_lvz_object_toggle(event.pname, [(76, True)])
            ssbot.send_reply("76 on")
            if event.command.id in [
                    self._sql_command_id, self._sqlnl_command_id]:

                # automatically addlimit or not
                limit = ""
                if event.command.id == self._sql_command_id:
                    limit = " limit 100"

                mt = self.getMessageTuple(event)

                db = self._db
                db.query(event.arguments_after[0] + limit, None, mt)

        elif event.type == EVENT_TICK:
            timer_expired = self.timer_man.getExpired()  # a timer expired
            # self.logger.info("tick")
            if timer_expired:
                # self.logger.info("timer expired")

                if timer_expired.data == 1:
                    # self.logger.info("1")
                    r = self._db.getResults()
                    if r:  # most of the time this will be None so check first
                        self.HandleResults(ssbot, event, r)
                    self.timer_man.set(1, 1)  # set it to check again in a sec
                elif timer_expired.data == 2:
                    # self.logger.info("2")
                    self._db.ping()
                    self.timer_man.set(300, 2)

    def HandleResults(self, ssbot, event, r):
        # message like connection error or connected
        if r.getType() == AElement.TYPE_MESSAGE:
            self.logger.info(r.message)
        else:
            r.GenericResultPrettyPrinter(
                ssbot, r.query.data[0], r.query.data[1])

    def cleanup(self):
        pass

# bot runs in this if not run by master u can ignore this
if __name__ == '__main__':
    bot_main(Bot, False, True, "99")
