"""
@author: The Junky

"""

import TimerManager
from Amysql import *

from subspace_bot.constants.commands import *
from subspace_bot.constants.messages import *
from subspace_bot.constants.events import *
from subspace_bot.helpers import bot_main
from subspace_bot.interface import BotInterface
from subspace_bot.utilities.loggers import LoggingRemoteHandler


class Bot(BotInterface):
    def __init__(self, bot, md):
        BotInterface.__init__(self, bot, md)
        bot.register_module_info(
            __name__,
            "MysqLtest",
            "The Junky",
            "egdldb helper",
            ".01b"
        )
        self._db = Amysql(self.logger)
        self._db.setDbCredentialsFromFile(
            self.module_path + R"/egdldb.conf", "db")
        self._db.start()
        self.clist = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_TEAM,
                      COMMAND_TYPE_FREQ, COMMAND_TYPE_PRIVATE,
                      COMMAND_TYPE_CHAT]
        self.commands = {
            # bot.register_command(
            #     '!sql',
            #     None,
            #     9,
            #     self.clist,
            #     "db",
            #     "[query]",
            #     'sql it zz'
            # ): (self.cmd_sql, ""),
            bot.register_command(
                '!sqlnl',
                None,
                9,
                self.clist,
                "db",
                "[query]",
                'sql it zz'
            ): (self.cmd_sql, "nl"),
            bot.register_command(
                '!addplayer',
                "!ap",
                5,
                self.clist,
                "egdl",
                "[name:vp:squadid]",
                'create/add new player to current league'
            ): (self.cmd_ap, ""),
            bot.register_command(
                '!changeplayer',
                "!cp",
                5,
                self.clist,
                "egdl",
                "[name:vp:squadid]",
                'update existing player'
            ): (self.cmd_cp, ""),
            bot.register_command(
                '!deleteplayer',
                "!dp",
                5,
                self.clist,
                "egdl",
                "[name]",
                'update existing player'
            ): (self.cmd_dp, ""),
            bot.register_command(
                '!listsquads',
                "!ls",
                5,
                self.clist,
                "egdl",
                "",
                'list squads'
            ): (self.cmd_ls, ""),
            bot.register_command(
                '!listplayers',
                "!lp",
                5,
                self.clist,
                "egdl",
                "[squad]",
                'list squads'
            ): (self.cmd_lp, "")
        }
        self.level = logging.DEBUG
        self.timer_man = TimerManager.TimerManager()
        self.timer_man.set(.01, 1)
        self.timer_man.set(300, 2)
        self.chat = bot.add_chat("st4ff")

        formatter = logging.Formatter('%(message)s')
        handler = LoggingRemoteHandler(logging.DEBUG, bot, "Ratio")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    @staticmethod
    def get_message_tuple(event):
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

    @staticmethod
    def cmd_sql(ssbot, event, param):
        ssbot.send_reply(event, "Disabled")
        return 0
        # if len(event.arguments) >= 1:
        #     if param and param == "nl":  # automatically addlimit or not
        #         limit = ""
        #     else:
        #         limit = " limit 100"
        #     mt = self.get_message_tuple(event)
        #     db = self._db
        #     db.query(event.arguments_after[0] + limit, None, mt)

    def cmd_ap(self, ssbot, event, param):
        if len(event.arguments) >= 1:
            mt = self.get_message_tuple(event)
            db = self._db
            q = """insert into egdl_players
            (userid, name, ip, machineid, vp, status, squad_id)
             values (0, %s, 0, 0, %s, 0, %s)
             """
            t = event.arguments_after[0].split(":")
            if len(t) != 3:
                ssbot.send_reply(event, "Could not parse 3 items")
            else:
                # print t
                db.query(q, (t[0], t[1], t[2]), mt)

    def cmd_cp(self, ssbot, event, param):
        mt = self.get_message_tuple(event)
        db = self._db
        q = "update egdl_players p set p.vp=%s, p.squad_id=%s where p.name=%s"
        t = event.arguments_after[0].split(":")
        if len(t) != 3:
            ssbot.send_reply(event, "Could not parse 3 items")
        else:
            # print t
            db.query(q, (t[1], t[2], t[0]), mt)

    def cmd_dp(self, ssbot, event, param):
        if len(event.arguments) >= 1:
            mt = self.get_message_tuple(event)
            db = self._db
            db.query(
                "delete from egdl_players where name=%s", (
                    event.arguments_after[0], ), mt
            )

    def cmd_ls(self, ssbot, event, param):
        mt = self.get_message_tuple(event)
        db = self._db
        db.query("Select s.* from egdl_squads s limit 100", None, mt)

    def cmd_lp(self, ssbot, event, param):
        if len(event.arguments) >= 1:
            mt = self.get_message_tuple(event)
            db = self._db
            db.query(
                "Select s.name, p.* from egdl_players p, egdl_squads s "
                "where s.name=%s and s.id=p.squad_id limit 100", (
                    event.arguments_after[0], ), mt
            )

    def handle_events(self, ssbot, event):
        if event.type == EVENT_COMMAND:
            if event.command.id in self.commands:
                c = self.commands[event.command.id]
                c[0](ssbot, event, c[1])

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
        self._db.cleanUp()

# bot runs in this if not run by master u can ignore this
if __name__ == '__main__':
    bot_main(Bot, False, True, "#egfdl")
