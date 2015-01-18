# Copyright (c) 2010 cycad <cycad@zetasquad.com>. All rights reserved.

# todo: bot.disconnect()
# todo: clean the interface between core and higher level disconnections

import socket
import sys
import array
import hashlib
import time
import zlib
import platform
import traceback
from logging import DEBUG, INFO, ERROR, CRITICAL

import os
from subspace import core_stack
from subspace.core_stack import get_tick_count_hs, tick_diff, CoreStack, \
    PRIORITY_HIGH
from subspace.settings import *
from subspace_bot.constants.events import *
from subspace_bot.constants.commands import *
from subspace_bot.constants.messages import *
from subspace_bot.constants.ships import *
from subspace_bot.constants.other import *
from subspace_bot.objects.ball import Ball
from subspace_bot.objects.brick import Brick
from subspace_bot.objects.command import Command
from subspace_bot.objects.flag import Flag
from subspace_bot.objects.game_event import GameEvent
from subspace_bot.objects.module_info import ModuleInfo
from subspace_bot.objects.op_list import Oplist
from subspace_bot.objects.player import Player
from subspace_bot.objects.timer import Timer


class SubspaceBot(core_stack.CoreStack):
    """The bot. Must be connected with connect_to_server() and then
    wait_for_event() must be called frequently for adequate performance.

    The typical bot's mainloop looks like:

    .. sourcecode:: python

        while bot.is_connected():
            event = bot.wait_for_event():
            if event.type = ...:
                ...
            elif event.type = ...:
                ...
    """

    def __init__(self, debug=False, is_master=False, mqueue=None, logger=None):
        """Initialize the CoreStack class. If debug is set debugging
        messages will be displayed."""
        CoreStack.__init__(self, debug, logger)
        self.__core_about = "Python-SubspaceBot By cycad <cycad@zetasquad.com>"
        self.__core_version = "0.002d"
        self.__debug = debug
        self.__players_by_pid = {}  # pid: Player
        self.__players_by_name = {}  # name: Player

        self.__event_list = []

        # generate a valid mid
        hash_string = os.name + sys.platform + socket.getfqdn()
        self.machine_id, self.permission_id = struct.unpack_from(
            'II', hashlib.md5(hash_string).digest())
        self.machine_id = self.__make_valid_machine_id(self.machine_id)

        self.players_here = []
        self.__players_by_name = {}
        self.__players_by_pid = {}

        self.__last_event_generated = None

        self.flag_list = [Flag(i) for i in range(MAX_FLAGS)]
        self.ball_list = [Ball(i) for i in range(MAX_BALLS)]

        self.pid = None
        self.name = None

        self.type = None
        self.description = None
        self.owner = None

        self.__connected = False

        self.arena = ""

        # added by junky
        self.__cmd_dict = {}
        self.__alias_dict = {}
        self.__category_dict = {}
        self.__module_info_list = []

        self.freq = None

        # the ships position data
        self.ship = None
        self.x_pos = 512 * 16
        self.y_pos = 512 * 16
        self.x_vel = 0
        self.y_vel = 0
        self.status = 0
        self.bounty = 0
        self.energy = 0
        self.rotation = 0

        self.__timer_list = []  # Timer()
        self.__next_timer_id = 0
        self.__last_timer_expire_tick = get_tick_count_hs()

        # used for formatting will store the max(len("!name/!alias [args]"))
        self.__max_cmd_len = 10

        self.__command_help_id = self.register_command(
            '!help',
            None,
            0,
            COMMAND_LIST_PP,
            "Core",
            "[<cat>|<!cmd>|*]",
            "display available commands"
        )
        self.__command_about_id = self.register_command(
            '!about',
            None,
            0,
            COMMAND_LIST_PP,
            "Core",
            "",
            "display information about current bot"
        )

        # for broadcasts it goes to master master distributes
        self.__mqueue = mqueue

        if is_master:
            self.__isMaster = True
            self.__command_die_id = self.register_command(
                '!stopmaster',
                None,
                7,
                COMMAND_LIST_PR,
                "Core",
                "",
                "stop the master"
            )
            self.__command_addop_id = self.register_command(
                '!Addop',
                "!ao",
                4,
                COMMAND_LIST_ALL,
                "Core",
                "[lvl:name]",
                "add a player to the oplist"
            )
            self.__command_delop_id = self.register_command(
                '!Delop',
                "!do",
                4,
                COMMAND_LIST_ALL,
                "Core",
                "[name]",
                "delete a player from the oplist"
            )
            self.__command_listops_id = self.register_command(
                '!Listops',
                "!lo",
                4,
                COMMAND_LIST_PP,
                "Core",
                "",
                "list all the ops = to your lvl"
            )
            self.__command_reloadops_id = self.register_command(
                '!Reloadops',
                "!ro",
                4,
                COMMAND_LIST_ALL,
                "Core",
                "",
                "reread oplist from file"
            )
        else:
            self.__isMaster = False
            self.__command_die_id = self.register_command(
                '!stopbot',
                "!die",
                2,
                COMMAND_LIST_ALL,
                "Core",
                "",
                "stop this bot"
            )
            self.__command_addop_id = None
            self.__command_delop_id = None
            self.__command_listops_id = None
            self.__command_reloadops_id = None

        # Event preprocessors can return a new event to pass on to
        # the bot, or None if no event should be generated
        self.__event_preprocessors = {
            # EVENT_START: self.__eventStartPreprocessor,
            EVENT_ENTER: self.__event_enter_preprocessor,
            EVENT_LEAVE: self.__event_leave_preprocessor,
            EVENT_TICK:  self.__event_tick_preprocessor,
            EVENT_CHANGE: self.__event_change_preprocessor,
            EVENT_DISCONNECT: self.__event_disconnect_preprocessor,
            EVENT_COMMAND: self.__event_command_preprocessor,
            EVENT_ARENA_LIST: self.__event_arena_list_preprocessor,
        }

        # event post processors
        self.__event_postprocessors = {

            EVENT_START: self.__event_start_postprocessor,
            EVENT_CHANGE: self.__neut_flags_carried_by_player_proccessor,
            EVENT_LEAVE: self.__neut_flags_carried_by_player_proccessor,
            EVENT_FLAG_PICKUP: self.__event_flag_pickup_postprocessor,
            EVENT_FLAG_DROP: self.__event_flag_drop_postprocessor,
            EVENT_KILL: self.__event_kill_postprocessor
        }

        # setup the appropriate handlers
        self.__packet_handlers = {
            0x03: self.__handle_player_entered_packet,
            0x04: self.__handle_player_left_packet,
            0x05: self.__handle_large_position_update_packet,
            0x06: self.__handle_kill_packet,
            0x07: self.__handle_message_packet,
            0x08: self.__handle_prize_packet,
            0x09: self.__handle_score_update_packet,
            0x0A: self.__handle_login_response_packet,
            0x0B: self.__handle_goal_packet,
            0x0D: self.__handle_freq_change_packet,
            0x0E: self.__handle_turret_packet,
            0x0F: self.__handle_arena_settings_packet,
            0x10: self.__handle_file_transfer,
            0x12: self.__handle_flag_update_packet,
            0x13: self.__handle_flag_pickup_packet,
            0x14: self.__handle_flag_victory_packet,
            0x16: self.__handle_flag_drop_packet,
            0x19: self.__handle_request_file,
            0x1A: self.__handle_score_reset_packet,
            0x1C: self.__handle_ship_change_packet_self,
            0x1D: self.__handle_ship_change_packet,
            0x1F: self.__handle_banner_packet,
            0x21: self.__handle_brick_drop_packet,
            0x22: self.__handle_turf_flag_update_packet,
            0x23: self.__handle_periodic_reward_packet,
            0x27: self.__handle_position_update_request,
            0x28: self.__handle_small_position_update_packet,
            0x29: self.__handle_map_information_packet,
            0x2A: self.__handle_compressed_map_packet,
            0x2C: self.__handle_koth_game_reset,
            0x2E: self.__handle_ball_position_packet,
            0x2F: self.__handle_arena_list_packet,
            0x31: self.__handle_login_packet,
            0x32: self.__handle_warpto_packet,
            0x38: self.__handle_watch_damage_packet,

        }

        self.__login_response = {
            0x00: "Login OK",
            0x01: "Unregistered Player",
            0x02: "Bad Password",
            0x03: "Arena is Full",
            0x04: "Locked Out of Zone",
            0x05: "Permission Only Arena",
            0x06: "Permission to Spectate Only",
            0x07: "Too many points to Play here",
            0x08: "Connection is too Slow",
            0x09: "Permission Only Arena",
            0x0A: "Server is Full",
            0x0B: "Invalid Name",
            0x0C: "Offensive Name",
            0x0D: "No Active Biller",
            0x0E: "Server Busy, try Later",
            0x10: "Restricted Zone",
            0x11: "Demo Version Detected",
            0x12: "Too many Demo users",
            0x13: "Demo Versions not Allowed",
            0xFF: "Restricted Zone, Mod Access Required"
        }

        self.__chats = []
        self.__chats_changed = False

        self.__oplist = Oplist()

        self.__started_time = time.time()

        # should the core download maps or not?
        self.__downloadLevelFiles = False

        # getaccesslevel will return 0 if biller is down
        self.billing = True

        self.settings = None

    def set_download_level_files(self, doit):
        """
            must set this to true if you want the core to download map files
        """
        self.__downloadLevelFiles = doit

    def __log(self, level, message):
        if self.logger:
            self.logger.log(level, message)
        else:
            print (message)

    def get_access_level(self, name):
        return self.__oplist.GetAccessLevel(name)

    def find_player_by_pid(self, pid):
        """Find a player by PID.

        If a player is not found, None is returned."""
        return self.__players_by_pid.get(pid)

    def find_player_by_name(self, name):
        """Find a player by name.

        If a player with the exact name is not found, None is returned."""
        return self.__players_by_name.get(name.lower())

    def register_command(self, name, alias, access_lvl, msg_types_list,
                         category, args, short_help, long_help=None):
        """Register a command with the core.

        name is the name of the command, including the '!'.
        description is a short one-line explanation of what the
        command does, displayed in !help.

        alias is a shortverion of the command like !sb for !startbot

        access_level is the min accesslevel you need to use this command

        msg_types_list is a list of message types this command supports
        for example [MESSAGE_TYPE_PRIVATE, MESSAGETYPE_PUBLIC, MSG_TYPE_CHAT]

        args will be displayed in help to tell users what arguments a
        command supports

        short_help will be displayed in !help category if the command is
        in a category

        long help only when u do !help !cmd

        Returns a unique identifier for the command, to be used in
        EVENT_COMMAND to identify the command being used."""
        kc = category.lower()
        k = name.lower()
        cmd_id = -1

        if args is None:
            args = ""
        if category is None:
            category = "None"
        if alias is None:
            alias = ""

        if k in self.__cmd_dict:
            self.__log(
                INFO, "Attempt to register already existing command: " + name)
        else:
            cmd_id = len(self.__cmd_dict)
            nc = Command(cmd_id, name, alias, access_lvl, msg_types_list,
                         category, args, short_help, long_help)
            self.__cmd_dict[k] = nc

            self.__max_cmd_len = max(
                len(nc.name) + len(nc.alias) + len(nc.args) + 4,
                self.__max_cmd_len
            )

            if alias is not None and alias != "":
                ka = alias.lower()
                if ka in self.__alias_dict:
                    self.__log(
                        INFO,
                        "Attempt to register already existing alias: " + ka
                    )
                else:
                    self.__alias_dict[ka] = nc

            if kc in self.__category_dict:
                self.__category_dict[kc].append(nc)
            else:
                self.__category_dict[kc] = [nc]

        return cmd_id

    def __get_cmd(self, name):
        name = name.lower()
        cmd = self.__cmd_dict.get(name) or self.__alias_dict.get(name)
        return cmd

    def set_bot_info(self, bot_type, description, owner):
        self.type = bot_type
        self.description = description
        self.owner = owner

    def register_module_info(
            self, filename, name, author, description, version):
        self.__module_info_list.append(
            ModuleInfo(filename, name, author, description, version))

    def __expire_timers(self):
        """Expires timers that are in the core's timer list."""
        now = get_tick_count_hs()
        self.__timer_list.sort(
            lambda a, b: int(
                (a.duration - tick_diff(now, a.base)) -
                (b.duration - tick_diff(now, b.base))
            )
        )

        while self.__timer_list:
            t = self.__timer_list[0]
            if tick_diff(now, t.base) == t.duration:
                event = GameEvent(EVENT_TIMER)
                event.id = t.id
                event.user_data = t.user_data
                self.__add_pending_event(event)
                self.__timer_list.pop(0)
            else:
                # since the timer list is sorted the timers after
                # are greater and dont need to be tested
                break

    def set_timer(self, seconds, user_data=None):
        """Sets a timer that will generate an EVENT_TIMER event in
        seconds seconds.

        user_data is passed back as event.user_data during EVENT_TIMER.

        Returns a unique timer id that is passed back in EVENT_TIMER's event.id
        when the timer expires."""
        timer_id = self.__next_timer_id
        self.__next_timer_id += 1
        self.__timer_list.append(Timer(timer_id, seconds, user_data))
        return timer_id

    def delete_timer(self, timer_id):
        self.__timer_list = [t for t in self.__timer_list if t.id != timer_id]

    # def deleteAllTimers(self):
    #    self.__timer_list = []

    @staticmethod
    def __make_valid_machine_id(machine_id):
        """Generates a valid machine ID."""
        # the mid has to be in a specific format
        mid = array.array('B', struct.pack('<I', machine_id))
        mid[0] %= 73
        mid[1] %= 129
        mid[3] = (mid[3] % 24) + 7
        return struct.unpack_from('<I', mid.tostring())[0]

    def connect_to_server(self, hostname, port, username, password,
                          arena='# master', new_connection=True):
        """Connect to a server using the Subspace protocol.

        hostname and port specify the hostname/IP address and port of
        the server to connect to.  username is the user to connect as.
        password is the combined password and SMod+ password
        seperated by an asterisk.  For example,
        'bot_password*smod_password'. Arena is the name of the arena
        to join upon entering the zone."""
        CoreStack.connect_to_server(self, hostname, port)
        self._queue_sync_request()
        self.flush_outbound_queues()
        self.__queue_login_packet(username, password)
        self.flush_outbound_queues()
        self.arena = arena
        self.__connected = True
        self.__last_pos_update_sent_tick = get_tick_count_hs()

    def __queue_login_packet(self, username, password):
        self.queue_packet(struct.pack(
            "<BB32s32sIBhHhIIIIII",
            0x09,
            0,
            username,
            password,
            self.machine_id,
            0,
            0,
            0x6f9d,
            0x86,
            444,
            555,
            self.permission_id, 0, 0, 0)
        )
        self.name = username

    def __queue_arena_login_packet(self, arena, ship_type=SHIP_SPECTATOR):
        join_type = 0xFFFD
        if arena.isdigit():
            join_type = int(arena)
        self.queue_packet(struct.pack(
            "<BBHHHH16s", 0x01, ship_type, 0, 4096, 4096, join_type, arena))

    def send_arena_message(self, message, sound=SOUND_NONE):
        """Send a message to the arena with an optional sound.

        message can be a list of messages to send."""
        msg = ["*arena " + m for m in message] if isinstance(message, list) \
            else "*arena " + message

        self._queue_message_packet(MESSAGE_TYPE_PUBLIC, msg, sound=sound)

    def send_public_message(self, message, sound=SOUND_NONE):
        """Send a public message with an optional sound.

        message can be a list of messages to send.

        Public messages are sent to the server reliably but may not be relayed
        from the server to all players reliably."""
        self._queue_message_packet(MESSAGE_TYPE_PUBLIC, message, sound=sound)

    def send_freq_message(self, freq, message):
        """Send a freq message.

        message can be a list of messages to send."""
        for p in self.players_here:
            if p.freq == freq:
                self._queue_message_packet(
                    MESSAGE_TYPE_FREQ, message, target_pid=p.pid)
                break

    def send_private_message(self, player, message, sound=SOUND_NONE):
        """Send a private message to player.
        player can be a Player object or the player's name
        message can be a list of messages to send.
        Only pass players to this function if you're doing alot of
        spamming qat once to ensure private Message is used instead
        of remote. if you pass a name the message will most likely
        be remote message"""

        # todo: player type should be deterministic - either string or instance

        pp = player if isinstance(player, Player) else \
            self.find_player_by_name(player)

        if pp:
            self._queue_message_packet(
                MESSAGE_TYPE_PRIVATE, message, target_pid=pp.pid, sound=sound)
        else:
            msg = [':' + player + ':' + m for m in message] if \
                isinstance(message, list) else ':' + player + ':' + message
            self._queue_message_packet(MESSAGE_TYPE_REMOTE, msg, sound=sound)

    def send_remote_message(self, player_name, message, sound=SOUND_NONE):
        """Send a Remote message to player.
        message can be a list of messages to send.
        if there is a player with the name in the arena it will priv
        instead of remote"""

        pn = player_name
        pp = self.find_player_by_name(pn)

        if pp:
            self._queue_message_packet(
                MESSAGE_TYPE_PRIVATE, message, target_pid=pp.pid, sound=sound)
        else:
            msg = [':' + pn + ':' + m for m in message] if \
                isinstance(message, list) else ':' + pn + ':' + message
            self._queue_message_packet(MESSAGE_TYPE_REMOTE, msg, sound=sound)

    def send_reply(self, event, message):
        """
        Convenience function, will only work in EVENT COMMAND
        you can use this function with out worrying how the command was used
        it will reply with priv/remote for most command types and on
        the chat it was contacted with if its a chat message
        """
        if event.command_type in [MESSAGE_TYPE_PUBLIC, MESSAGE_TYPE_PRIVATE,
                                  MESSAGE_TYPE_TEAM, MESSAGE_TYPE_FREQ,
                                  MESSAGE_TYPE_ALERT]:
            self.send_private_message(event.player, message)
        elif event.command_type == MESSAGE_TYPE_REMOTE:
            self.send_private_message(event.pname, message)
        elif event.command_type == MESSAGE_TYPE_CHAT:
            # if event.chat_no  in [8, 10]:
            #    self.send_chat_message(""+str(event.chat_no)+""+message)
            # else:
            #    self.send_chat_message(""+str(event.chat_no)+""+message)
            self.send_chat_message("" + str(event.chat_no) + "" + message)

    def send_team_message(self, message, sound=SOUND_NONE):
        """Send a team message."""
        self._queue_message_packet(MESSAGE_TYPE_TEAM, message, sound=sound)

    def send_chat_message(self, message, sound=SOUND_NONE):
            self._queue_message_packet(MESSAGE_TYPE_CHAT, message, sound=sound)

    def add_chat(self, chat):
        """
        multiple modules may be adding chats to a bot, this is an ez
        way for modules to know which chat is relevant to them
        input: chat can be a single chat or a list of chats, or a
        string that contains a list of chats output: a list of of
        numbers, 1 for each chat you passed in

        Note: if you only added one chat then the list will contain
        only one int if there are more than 10 chats this function
        will return -1 for all chats it couldnt add
        """
        rc = []
        if isinstance(chat, list):
            lc = chat
        else:
            lc = chat.split(", ")

        for c in lc:
            c = c.lower().strip()
            existing_chat = self.get_chat_number(c)
            if existing_chat != -1:
                rc.append(existing_chat)
            else:
                if len(self.__chats) >= 10:
                    rc.append(-1)
                else:
                    self.__chats.append(c)
                    rc.append(len(self.__chats))
                    self.__chats_changed = True
        return rc

    def get_chat_number(self, chat_):
        """
        get the channel number for any given chat if it is in the list
        else it will return -1
        """
        i = 0
        chat = chat_.lower()
        for c in self.__chats:
            i += 1
            if c == chat:
                return i
        return -1

#   def send_message(self, message_type, message,
#                   target=None, sound=SOUND_NONE):
#        if message_type == MESSAGE_TYPE_PUBLIC
#            self.send_private_message(event.player, message)
#        elif message_type == MESSAGE_TYPE_PRIVATE:
#        elif message_type == MESSAGE_TYPE_FREQ:
#            if type(target) != int
#        elif message_type == MESSAGE_TYPE_TEAM:
#        elif message_type == MESSAGE_TYPE_REMOTE:
#            self.send_private_message(event.pname, message)
#        elif message_type == MESSAGE_TYPE_CHAT:
#            self.send_chat_message(message)

    def _queue_message_packet(self, message_type, message,
                              target_pid=PID_NONE, sound=SOUND_NONE):
        # this isnt exposed because its a bit too complicated,
        # the simpler calls are exposed that
        # deal with basic message types and are easier to use.
        # lets make this private
        if isinstance(message, list):
            for m in message:
                self.queue_packet(struct.pack(
                    "<BBBH",
                    0x06,
                    message_type,
                    sound,
                    target_pid) + m[:247] + '\x00', reliable=True)
        else:
            self.queue_packet(struct.pack(
                "<BBBH",
                0x06,
                message_type,
                sound,
                target_pid) + message[:247] + '\x00', reliable=True)

    def send_module_event(self, source, name, data):
        """
        this function is so modules can share information with each
        other for example info bot will parse info
        and trigger this event
        if another module wanst to use the parsed info it knows the
        event_data is info and can use it accordingly
        if data is likly to change the data should be deep coped b4
        being used
        if you are going to store the data deep copy it
        """
        event = GameEvent(EVENT_MODULE)
        event.event_source = source
        event.event_name = name
        event.event_data = data
        self.__add_pending_event(event)

    def send_broadcast(self, message):  # used by bots/modules
        """
        a way for bots to send text messages to all other bots
        connected to the master
        """
        event = GameEvent(EVENT_BROADCAST)
        event.bsource = self.name
        event.bmessage = message
        if self.__mqueue:  # if is being used as a module in master
            self.__mqueue.queue(event)  # send to master for distribution
        else:
            self.__add_pending_event(event)  # else queue back to the core

    # used by master to queue back the broadcasts
    def queue_broadcast(self, event):
        self.__add_pending_event(event)

    def spectate_player(self, player):
        # sets the bot to spectate specified player.
        # IMPORTANT: does not change the bot's position. this only
        # tells the server you wish to recieve position update packets
        # from target player.
        # if you wish to follow the player around, must use
        # SubspaceBot's set_position() function for each recieved
        # position update packet from target player.
        if not isinstance(player, Player):
            player = self.find_player_by_name(player)
        self.__queue_spec_player_packet(player)

    def unspectate_player(self):
        # unspectates player, if any is spectated.
        self.__queue_spec_player_packet(None)

    def __queue_spec_player_packet(self, player):
        if player and player.ship != SHIP_SPECTATOR:
            self.queue_packet(struct.pack("<BH", 0x08, player.pid),
                              reliable=True)
        else:
            self.queue_packet(struct.pack("<BH", 0x08, 0xFFFF), reliable=True)

    def set_bot_banner(self, banner):
        """Sets the bots banner to banner given as an argument. Banner
        is a 96 byte array."""
        self.__queue_banner_packet(banner)

    def __queue_banner_packet(self, banner):
        packet = struct.pack("<B", 0x19) + banner
        self.queue_packet(packet, reliable=True)

    def send_death_packet(self, pp):
        """Tells the bot to queue a death packet to the server, with
        pid being the killer."""
        pid = self.__to_pid(pp)
        self.__queue_death_packet(pid)

    def __queue_death_packet(self, pid):
        packet = struct.pack("<BHH", 0x05, pid, self.bounty)
        self.queue_packet(packet, reliable=True)

    def __handle_login_packet(self, packet):  # packet is not used
        self.__queue_arena_login_packet(self.arena)
        self.flush_outbound_queues()
        self.__add_pending_event(GameEvent(EVENT_START))

    def __event_start_postprocessor(self, event):
        if len(self.__chats) > 0:
            cstr = "?chat="
            for c in self.__chats:
                cstr += c + ", "
            self.send_public_message(cstr)
            self.__chats_changed = False
        self.send_public_message("?arena")
        return event

    def __handle_player_entered_packet(self, packet):
        # this should really create a player here
        # dictionary (pid -> player object)
        while len(packet) >= 64:
            ptype, ship, audio, name, squad, fp, kp, pid, freq, w, l, \
                turreted, flags_carried, koth = \
                struct.unpack_from("<BBB20s20sIIHHHHHHB", packet)
            name = name.split(chr(0))[0]
            squad = squad.split(chr(0))[0]
            player = Player(name, squad, pid, ship, freq)
            player.kill_points = kp
            player.flag_points = fp
            player.wins = w
            player.losses = l
            player.flag_count = flags_carried
            player.turreted_pid = turreted
            # t = self.find_player_by_pid(turreted)
            # self.send_public_message("Entered %s turreting %s:%x"%(name,
            #   t.name if t else "None", turreted ))
            # if t:
            #    t.turreter_list.append(turreted)
            # else
            #    self.__log(INFO, "EventEnter:Turreted pid not
            #       found:%x"%(turreted))
            event = GameEvent(EVENT_ENTER)
            event.player = player
            self.__add_pending_event(event)
            packet = packet[64:]

    def __handle_goal_packet(self, packet):
        ptype, freq, points = struct.unpack_from("<BHI", packet)
        event = GameEvent(EVENT_GOAL)
        event.freq = freq
        event.points = points
        self.__add_pending_event(event)

    def __handle_ball_position_packet(self, packet):
        ptype, ball_id, x_pos, y_pos, x_vel, y_vel, pid, ptime = \
            struct.unpack_from("<BBHHhhHI", packet)
        event = GameEvent(EVENT_BALL)
        event.ball_id = ball_id
        event.x_pos = x_pos
        event.y_pos = y_pos
        event.x_vel = x_vel
        event.y_vel = y_vel
        event.player = self.find_player_by_pid(pid)
        event.time = ptime
        # move to post processor
        b = self.ball_list[ball_id]
        b.x = x_pos
        b.y = y_pos
        b.pid = pid
        b.time = ptime
        self.__add_pending_event(event)

    def __handle_flag_update_packet(self, packet):  # 0x12
        ptype, flag_id, x, y, freq = struct.unpack_from("<BHHHH", packet)
        event = GameEvent(EVENT_FLAG_UPDATE)
        event.freq = freq
        event.flag_id = flag_id
        event.x = x
        event.y = y
        # move to postprocessor
        f = self.flag_list[flag_id]
        f.freq = freq
        f.x = x
        f.y = y
        self.__add_pending_event(event)

    def __handle_flag_victory_packet(self, packet):  # 0x14
        ptype, freq, points = struct.unpack_from("<BHL", packet)
        event = GameEvent(EVENT_FLAG_VICTORY)
        event.freq = freq
        event.points = points
        for f in self.flag_list:
            f.freq = FREQ_NONE
            f.x = COORD_NONE
            f.y = COORD_NONE
        # addpostprocessor and reset flag state
        self.__add_pending_event(event)

    def __handle_score_update_packet(self, packet):
        ptype, pid, flag_points, kill_points, wins, losses = \
            struct.unpack_from("<BHLLHH", packet)
        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_SCORE_UPDATE)
            # event.pid = pid
            event.old_flag_points = player.flag_points
            event.old_kill_points = player.kill_points
            event.old_wins = player.wins
            event.old_losses = player.losses

            player.flag_points = flag_points
            player.kill_points = kill_points
            player.wins = wins
            player.losses = losses
            event.player = player
            self.__add_pending_event(event)

    def __handle_prize_packet(self, packet):
        ptype, time_stamp, x, y, prize, pid = \
            struct.unpack_from("<BLHHHH", packet)
        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_PRIZE)
            event.time_stamp = time_stamp
            event.x = x
            event.y = y
            event.prize = prize
            event.player = player
            player.x = x
            player.y = y
            self.__add_pending_event(event)

    def __handle_flag_pickup_packet(self, packet):
        ptype, flag_id, pid = struct.unpack_from("<BHH", packet)
        player = self.find_player_by_pid(pid)
        if player:
            flag = self.flag_list[flag_id]
            event = GameEvent(EVENT_FLAG_PICKUP)
            event.player = player
            event.flag_id = flag_id
            event.flag = flag
            # self.send_public_message("fp/ft %d:%x->%x"%(flag_id,
            #   flag.carried_by_pid, pid))
            self.__add_pending_event(event)

    @staticmethod
    def __event_flag_pickup_postprocessor(event):
        event.flag.x = COORD_NONE
        event.flag.y = COORD_NONE
        event.player.flag_count += 1
        event.flag.freq = event.player.freq

    def __handle_flag_drop_packet(self, packet):
        ptype, pid = struct.unpack_from("<BH", packet)
        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_FLAG_DROP)
            event.player = player
            # move to post processor
            event.flag_count = player.flag_count
            self.__add_pending_event(event)

    @staticmethod
    def __event_flag_drop_postprocessor(event):
        player = event.player
        player.flag_count = 0

    def __handle_score_reset_packet(self, packet):
        ptype, pid = struct.unpack_from("<BH", packet)
        # player = self.find_player_by_pid(pid)
        event = GameEvent(EVENT_SCORE_RESET)
        event.player = None
        event.pid = pid
        # move to post ptocessor
        if pid == 0xFFFF:
            for p in self.players_here:
                p.kill_points = 0
                p.flag_points = 0
                p.wins = 0
                p.losses = 0
        else:
            p = self.find_player_by_pid(pid)
            if p:
                p.kill_points = 0
                p.flag_points = 0
                p.wins = 0
                p.losses = 0
                event.player = p
        self.__add_pending_event(event)

    def __handle_turret_packet(self, packet):
        ptype, turreter_pid, turreted_pid = struct.unpack_from("<BHH", packet)
        turreter = self.find_player_by_pid(turreter_pid)
        turreted = self.find_player_by_pid(turreted_pid)

        event = GameEvent(EVENT_TURRET)
        event.turreter = turreter
        event.turreted = turreted
        if turreter:
            if turreter.turreted_pid == 0xFFFF:
                event.old_turreted = None
            else:
                event.old_turreted = self.find_player_by_pid(
                    turreter.turreted_pid)
            turreter.turreted_pid = turreted_pid
            self.__add_pending_event(event)

    def __handle_arena_settings_packet(self, packet):
        self.settings = ArenaSettings(packet)

    def __handle_periodic_reward_packet(self, packet):
        packet = packet[1:]
        point_list = []
        if len(packet) >= 4:
            while len(packet) >= 4:
                freq, points = struct.unpack_from("<HH", packet)
                point_list.append((freq, points))
                packet = packet[4:]
                # todo: add points to all the player structs post event

            event = GameEvent(EVENT_PERIODIC_REWARD)
            event.point_list = point_list
            self.__add_pending_event(event)

    def __handle_turf_flag_update_packet(self, packet):
        packet = packet[1:]
        i = 0
        while len(packet) >= 2:
            self.flag_list[i].freq = struct.unpack_from("H", packet)
            packet = packet[2:]
            i += 1

    def __handle_speed_game_over(self, packet):
        ptype, best, mr, msc, sc1, sc2, sc3, sc4, sc5, p1, p2, p3, p4, p5 = \
            struct.unpack_from("BBHIIIIIIHHHHH", packet)
        event = GameEvent(EVENT_SPEED_GAME_OVER)
        event.best = best
        event.bot_rank = mr
        event.bot_score = msc
        event.winners = [
            (1, self.find_player_by_pid(p1), sc1),
            (2, self.find_player_by_pid(p2), sc2),
            (3, self.find_player_by_pid(p3), sc3),
            (4, self.find_player_by_pid(p4), sc4),
            (5, self.find_player_by_pid(p5), sc5),
        ]

    def __handle_banner_packet(self, packet):
        # commented out stuff is if you wish to save the banner as an int array
        ptype, pid = struct.unpack_from("<BH", packet)
        # banner = []
        packet = packet[3:]
        player = self.find_player_by_pid(pid)
        if player:
            player.banner = packet

    # def __handleObjectMovePacket(self, packet):
    #    # uncomment for debugging, must add 0x36:
    #       self.__handleObjectMovePacket, to dictionary before uncommenting
    #    print (packet.encode('hex'))
    #    type, changeflags, rand, x, y, image, layer, timemode = \
    #       struct.unpack_from("<BBHhhBBH", packet)
    #    # print ('change flags: ' + self.int2bin(changeflags, 8))
    #    print ('object id: ' + str((rand & 0xFFFE) >> 1))
    #    print ('map value: ' + str(rand & 0x0001))
    #    print ('x: ' + str(x))
    #    print ('y: ' + str(y))
    #    print ('image: ' + str(image))
    #    print ('layer: ' + str(layer))
    #    print ('timemode: ' + str(timemode))

    def __to_pid(self, pp):
        if pp is None:
            pid = 0xFFF
        elif isinstance(pp, int):
            pid = pp
        elif isinstance(pp, str):
            p = self.find_player_by_name(pp)
            if p:
                pid = p.pid
            else:
                raise Exception(
                    "__to_pid recieved a string, but player not found")
        elif isinstance(pp, Player):
            pid = pp.pid
        else:
            raise Exception("__topid recieved unknown type" + pp)
        return pid

    def send_map_object_move(self, pp, changeflags, x_pos, y_pos,
                             objectidandtype, imageid, layer, timemode):
        # currently only moves a MAPOBJECT in an LVZ, please use the LVZObject
        # class and run updates through it.
        pid = self.__to_pid(pp)
        packet = struct.pack(
            "<BHBBHhhBBH",
            0x0A,
            pid,
            0x36,
            changeflags,
            objectidandtype,
            x_pos,
            y_pos,
            imageid,
            layer,
            timemode
        )
        self.queue_packet(packet)

    def send_lvz_object_toggle(self, pp, list_of_tuples):
        """"
        pp can be PID_NONE to send to entire arena
        the list of tuples has to be  [(id, on/off), (id2, on, off), etc]
        For example: turn on obj 3333 and off 3334
        ssbot.send_lvz_object_toggle(player, [(3333, True), (3334, False)])
        """
        packet = struct.pack(
            "<BHB",
            0x0A,
            PID_NONE if pp == PID_NONE else self.__to_pid(pp),
            0x35
        )
        for objtoggletuple in list_of_tuples:
            packet += struct.pack(
                "<H",
                (objtoggletuple[0] & 0x7FFF) if objtoggletuple[1] else
                (objtoggletuple[0] | 0x8000)
            )
        self.queue_packet(packet)

    def __handle_player_left_packet(self, packet):
        # this should really use a player here dictionary and add the
        # player info to the event
        ptype, pid = struct.unpack_from("<BH", packet)
        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_LEAVE)
            event.player = player
            self.__add_pending_event(event)

    def __handle_login_response_packet(self, packet):
        login_response, = struct.unpack_from("<B", packet, 1)
        # print self.__login_response[login_response]
        if login_response == 0x01:
            self.__send_registration_form()  # doesnt work
            self.__log(INFO, "Sending Registration Form")
        elif login_response in [0x00, 0x05, 0x06]:
            pass
        elif login_response == 0x0D:  # biller down
            self.billing = False
        elif login_response == 0x0E:
            self.__log(DEBUG, "Server Busy, try again later")
            self.__connected = False
        else:
            raise Exception(
                "Login Error:%s" % self.__login_response[login_response])

    def __handle_ship_change_packet(self, packet):
        ptype, ship, pid, freq = struct.unpack_from("<BBHH", packet)

        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_CHANGE)
            event.new_freq = freq
            event.new_ship = ship
            event.player = player
            if pid == self.pid:
                self.freq = freq
                self.ship = ship
            self.__add_pending_event(event)

    def __handle_freq_change_packet(self, packet):
        ptype, pid, freq, unused = struct.unpack_from("<BHHB", packet)

        player = self.find_player_by_pid(pid)
        if player:
            event = GameEvent(EVENT_CHANGE)
            event.new_freq = freq
            event.new_ship = player.ship
            event.player = player
            if pid == self.pid:
                self.freq = freq
                self.ship = player.ship
            self.__add_pending_event(event)

    @staticmethod
    def __neut_flags_carried_by_player_proccessor(event):
        """
            set flags carried by event_player to neuted
        """
        p = event.player
        p.flag_count = 0

    def __handle_ship_change_packet_self(self, packet):
        """Handle a ship change packet for the bot itself."""
        ptype, ship = struct.unpack_from("<BB", packet)

        player = self.find_player_by_pid(self.pid)
        if player:
            event = GameEvent(EVENT_CHANGE)
            event.new_freq = player.freq
            event.new_ship = ship
            event.player = player
            self.__add_pending_event(event)

    def __handle_message_packet(self, packet):
        ptype, message_type, sound, pid = struct.unpack_from("<BBBH", packet)
        message = packet[5:].split(chr(0))[0]
        message_name = None
        chatnum = None
        alert = None
        arena = None
        player = None
        # added by junky
        if message_type == MESSAGE_TYPE_REMOTE:
            i = message.find(": (")
            i2 = message.find(") (")
            i3 = message.find("): ")
            if i != -1 and i2 != -1 and i3 != -1:  # alert
                alert = message[0:i]
                message_name = message[i+3:i2]
                arena = message[i2 + 3:i3]
                message = message[i3 + 3:]
                message_type = MESSAGE_TYPE_ALERT
            else:
                i = message.find(")>")
                message_name = message[1:i]
                i += 2
                message = message[i:]
        elif message_type == MESSAGE_TYPE_CHAT:
            i = message.find(":")
            chatnum = int(message[0:i])
            i2 = message.find(">")
            message_name = message[i+1:i2]

            i2 += 1
            message = message[i2+1:]
        elif message_type in [MESSAGE_TYPE_PUBLIC_MACRO,
                              MESSAGE_TYPE_PUBLIC,
                              MESSAGE_TYPE_TEAM,
                              MESSAGE_TYPE_FREQ,
                              MESSAGE_TYPE_PRIVATE,
                              MESSAGE_TYPE_WARNING]:
            player = self.find_player_by_pid(pid)
            if player:
                message_name = player.name
            else:
                self.__log(
                    DEBUG,
                    "WTF:MESSAGE mtype%i pid 0x%x:%s" %
                    (message_type, pid, message)
                )
                message_name = ""

        # add the message event
        event = GameEvent(EVENT_MESSAGE)
        event.player = player
        event.message = message
        event.message_type = message_type
        event.pname = message_name
        event.chat_no = chatnum
        event.alert_name = alert
        event.alert_arena = arena

        self.__add_pending_event(event)

        # add the command event
        if len(message) > 0 and message[0] == '!' and message_type in \
                COMMAND_LIST_ALL:
            command = message.split()[0]
            arguments = message.split()[1:]
            arguments_after = []

            for index in xrange(0, min(8, len(arguments))):
                arguments_after.append(' '.join(arguments[index:]))
                if index > 8:
                    break

            event = GameEvent(EVENT_COMMAND)
            event.player = player
            event.command = command
            event.arguments = arguments
            event.arguments_after = arguments_after
            event.pname = message_name
            if event.pname:
                event.plvl = self.get_access_level(event.pname)
            else:
                event.plvl = 0
            event.chat_no = chatnum
            event.alert_name = alert
            event.alert_arena = arena
            event.command_type = message_type

            self.__add_pending_event(event)

    def __handle_command_die(self, event):
        self.send_reply(event, "Ok")
        if self.__isMaster:
            self.__log(CRITICAL, "MasterBot shutdown by %s" % (event.pname, ))
        else:
            self.__log(INFO, "%s stopped by %s" % (self.name, event.pname))

        self.disconnect_from_server()

    def __handle_command_about(self, event):
        self.send_reply(
            event,
            "Interpreter:%s version:%s" % (
                platform.python_implementation(), platform.python_version())
        )
        self.send_reply(event, "Core:"+self.__core_about)
        self.send_reply(event, "Core Version:"+self.__core_version)
        self.send_reply(event, "BotType:%-10s owner:%-10s" % (
            self.type, self.owner))
        self.send_reply(event, "About:%s" % (
            self.description))
        for m in self.__module_info_list:
            self.send_reply(
                event,
                "Modules:%10s: %10s:%10s by %10s\t\t %50s" % (
                    m.filename, m.name, m.version, m.author, m.description)
            )

    def __handle_command_help(self, event):
        if len(event.arguments_after) > 0:
            # make format string based on max cmd size
            fmt = '%' + '-' + str(self.__max_cmd_len) + "s   %s"

            if event.arguments_after[0][0] == '*':
                self.send_reply(event, "All commands:")
                for k, v in self.__cmd_dict.iteritems():
                    if v.alias != "":
                        alias = "/" + v.alias
                    else:
                        alias = ""
                    self.send_reply(
                        event,
                        fmt % (v.name + alias + " " + v.args, v.help_short)
                    )
            elif event.arguments_after[0][0] == '!':
                command = self.__get_cmd(event.arguments_after[0])
                if command:
                    self.send_reply(event, "Extended help for command:")
                    self.send_reply(event, "Name:%10s Alias:%10s" % (
                        command.name, command.alias))
                    self.send_reply(event, "Accepted Arguments:%s" % (
                        command.args))
                    if command.help_long:
                        for m in command.help_long.split("\n"):
                            self.send_reply(event, m)
                    else:

                        self.send_reply(
                            event,
                            ("This command doesnt have extended help defined"
                             " for it")
                        )
                else:
                    self.send_reply(event, "unknown command:")
            else:
                name = event.arguments_after[0].lower()
                cat = self.__category_dict.get(name)
                if cat:
                    self.send_reply(event, "commands in %s:" % name)
                    for v in cat:
                        if v.alias != "":
                            alias = "/" + v.alias
                        else:
                            alias = ""
                        self.send_reply(
                            event,
                            fmt % (v.name + alias + " " + v.args, v.help_short)
                        )
                else:
                    self.send_reply(event, "no such category exists (%s):" % (
                        name))
        else:
            self.send_reply(event, "commands:")
            for k, v in self.__category_dict.iteritems():
                i = 1
                out = ""
                for e in v:
                    if i % 6 == 0:
                        self.send_reply(event, k + ": " + out[1:])
                        out = ""
                        i = 1
                    i += 1
                    out += ", " + e.name
                if len(out) > 0:
                    self.send_reply(event, k + ": " + out[1:])

    def __handle_command_add_op(self, event):
        if (len(event.arguments_after) > 0
                and len(event.arguments_after[0]) > 3
                and event.arguments_after[0][0].isdigit()
                and event.arguments_after[0][1] in [':', ' ']):

            lvl = int(event.arguments_after[0][0])
            name = event.arguments_after[0][2:]
            if lvl <= 0 or lvl > 9:
                self.send_reply(
                    event,
                    "Error:Invalid Level must be between 0 1 and 9"
                )
                return
            if self.get_access_level(name) > event.plvl:
                self.send_reply(
                    event,
                    ("ERROR:ACCESS DENIED:%s is already an op and has = "
                     "access than you do" % name)
                )
                return
            rc = self.__oplist.AddOp(lvl, name)
            if rc:
                self.send_reply(event, "Success")
                self.__log(INFO, "%s added op %s with %d level" % (
                    event.pname, name, lvl))
            else:
                self.send_reply(event, "Failure")

        else:
            self.send_reply(event, "invalid syntax use: !addop lvl:name")

    def __handle_command_del_op(self, event):
        if len(event.arguments_after) > 0:
            name = event.arguments_after[0]
            if self.get_access_level(name) >= event.plvl:
                self.send_reply(
                    event,
                    ("ERROR:ACCESS DENIED:You Can only delete ops who have "
                     "lower levels")
                )
                return
            rc = self.__oplist.DelOp(name)
            if rc:
                self.send_reply(event, "Success")
                self.__log(INFO, "%s deleted op %s" % (event.pname, name))
            else:
                self.send_reply(event, "Failure")

        else:
            self.send_reply(event, "invalid syntax use: !addop lvl:name")

    def __handle_command_list_ops(self, event):
        self.__oplist.ListOps(self, event)

    def __handle_command_reload_ops(self, event):
        rc = self.__oplist.Read()
        if rc:
            self.send_reply(event, "Success")
            self.__log(INFO, "%s reloaded oplist" % (event.pname, ))
        else:
            self.send_reply(event, "Failure")

    def __event_enter_preprocessor(self, event):
        # xxx we should probably make sure the player doesnt already exist here
        player = event.player
        self.__players_by_name[player.name.lower()] = player
        self.__players_by_pid[player.pid] = player
        # make sure player does not already exist in the list
        self.players_here = [p for p in self.players_here
                             if p.pid != player.pid]
        self.players_here.insert(0, player)

        if player.name.lower() == self.name.lower():
            self.pid = player.pid
            self.ship = player.ship
            self.freq = player.freq
            self.send_private_message(player, "*bandwidth 10000")
            self.send_public_message("*relkills 1")
            self.__add_pending_event(GameEvent(EVENT_LOGIN))

        return event

    def __event_leave_preprocessor(self, event):
        self.__players_by_name.pop(event.player.name.lower(), None)
        self.__players_by_pid.pop(event.player.pid, None)
        self.players_here = [p for p in self.players_here
                             if p.pid != event.player.pid]

        return event

    def __event_tick_preprocessor(self, event):
        # send pos update
        now = get_tick_count_hs()
        # xxx this will need to be changed later if the bot is out of ship
        # (10hs interval if out of ship)

        # update position every 10 hs if in ship, otherwise every 1 second
        if self.ship is not None:
            time_period = 100 if self.ship == SHIP_SPECTATOR else 10
            if tick_diff(now, self.__last_pos_update_sent_tick) > time_period:
                self.__queue_position_update_packet()
                self.__last_pos_update_sent_tick = now

        if tick_diff(now, self.__last_timer_expire_tick) > 100:
            self.__expire_timers()
            self.__last_timer_expire_tick = now

        # if chats have been added redo the ?Chat command
        if self.__chats_changed and self.is_connected():
            cstr = "?chat="
            for c in self.__chats:
                cstr += c + ", "
            self.send_public_message(cstr, 0)
            self.__chats_changed = False

        return event

    def __event_change_preprocessor(self, event):
            # update the players freq and ship
            player = event.player

            # if this is the bots own info, update it
            if player.pid == self.pid:
                self.ship = event.new_ship
                self.freq = event.new_freq

            new_event = GameEvent(EVENT_CHANGE)
            new_event.player = player
            new_event.old_freq = player.freq
            new_event.old_ship = player.ship

            player.ship = event.new_ship
            player.freq = event.new_freq

            return new_event

    def __event_disconnect_preprocessor(self, event):
        self.__connected = False
        return event

    def __event_command_preprocessor(self, event):
        command = self.__get_cmd(event.command)

        if command is None:
            if event.command_type in [
                    COMMAND_TYPE_PRIVATE, COMMAND_TYPE_REMOTE]:
                self.send_reply(event, "Unknown command")
            return None

        new_event = None
        if not command.is_allowed(event.command_type):
            return None

        if event.plvl >= command.access_level:
            # this player is allowed to use the command
            new_event = GameEvent(EVENT_COMMAND)
            new_event.player = event.player
            new_event.command = command
            new_event.arguments = event.arguments
            new_event.arguments_after = event.arguments_after
            new_event.pname = event.pname
            new_event.plvl = event.plvl
            new_event.chat_no = event.chat_no
            new_event.alert_name = event.alert_name
            new_event.alert_arena = event.alert_arena
            new_event.command_type = event.command_type

            if command.id == self.__command_die_id:
                self.__handle_command_die(new_event)
            elif command.id == self.__command_help_id:
                self.__handle_command_help(new_event)
            elif command.id == self.__command_about_id:
                self.__handle_command_about(new_event)
            elif self.__isMaster:
                if command.id == self.__command_addop_id:
                    self.__handle_command_add_op(new_event)
                elif command.id == self.__command_delop_id:
                    self.__handle_command_del_op(new_event)
                elif command.id == self.__command_listops_id:
                    self.__handle_command_list_ops(new_event)
                elif command.id == self.__command_reloadops_id:
                    self.__handle_command_reload_ops(new_event)
            else:
                event.command = command
        else:
            self.send_reply(event,  "Access denied")

        return new_event

    def __event_arena_list_preprocessor(self, event):
        # preprocess the negative count
        new_event = GameEvent(EVENT_ARENA_LIST)
        new_event.arena_list = []

        for arena, count in event.arena_list:
            if count < 0:
                count = abs(count)
                here = 1
                self.arena = arena
            else:
                here = 0

            new_event.arena_list.append((arena, count, here))

        return new_event

    def is_connected(self):
        """Returns True if the bot is connected to the
        server, otherwise False."""
        return self.__connected

    def __handle_position_update_request(self, packet):
        self.__queue_position_update_packet()

    def __queue_position_update_packet(self, weapons=0):
        """Queue a position update packet to the server."""
        checksum = 0

        packet = struct.pack(
            "<BBIhHBBHhHHH",
            0x03,
            self.rotation,
            get_tick_count_hs(),
            self.x_vel,
            self.y_pos,
            checksum,
            self.status,
            self.x_pos,
            self.y_vel,
            self.bounty,
            self.energy,
            weapons
        )
        for b in packet:
            checksum = ord(b)

        packet = packet[:10] + chr(checksum) + packet[11:]

        self.queue_packet(packet, priority=PRIORITY_HIGH)
        self.__last_pos_update_sent_tick = get_tick_count_hs()

    def set_position(self, x_pos=8192, y_pos=8192,
                     x_vel=0, y_vel=0, rotation=0,
                     status_flags=0, bounty=1000, energy=1000):
        """Set the bot's coordinates and other position data and send
        the new position to the server.

        status_flags is made of combinations of STATUS_Xxx.

        When this is called a packet is queued for send immediately."""
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.status = status_flags
        self.bounty = bounty
        self.energy = energy
        self.rotation = rotation
        self.__queue_position_update_packet()

    @staticmethod
    def make_weapons(wtype, lvl, shrapb, shraplvl, shrap, alternate):
        """
        this function will create a weapons struct to pass to sendfireweapon
        wtype  is WEAPON_XX
        lvl can be 0-3
        shrap_b 0, 1 indicates if the weapon has bouncing shrapnal
        shraplvl 0-3
        shrap 0-31
        alternate can be 0, 1
            if firing bombs 0 for bombs 1 for mines
            if firing bullets 0 for single gun 1 for multifire
        """
        return ((alternate << 15) | (shrap << 10) | (shraplvl << 8) |
                (shrapb << 7) | (lvl << 5) | wtype)

    def send_fire_weapon(self, x_pos=8192, y_pos=8192, x_vel=0, y_vel=0,
                         rotation=0, status_flags=0, bounty=1000,
                         energy=1000, weapons=0):
        """
        same as setposition if weapons is not passed
        see WEAPON_XX and make_weapons function
        """
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.status = status_flags
        self.bounty = bounty
        self.energy = energy
        self.rotation = rotation
        self.__queue_position_update_packet(weapons)

    def send_drop_brick(self, x, y):
        """
        this function will make the bot drop a brick in the specified location
        unfortunatly we cannot control the orientation of the dropped brick
        x, y are in pixels not tiles conversion done by this function
        """
        x >>= 4
        y >>= 4
        packet = struct.pack("<BHH", 0x1C, x, y)
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_freq_change(self, freq):
        """Sends a freq change request to the server.

        Note that until you receive an EVENT_CHANGE update for the bot,
        your freq has not changed."""

        packet = struct.pack("<BH", 0x0F, freq)
        self.queue_packet(packet, priority=PRIORITY_HIGH)

    @staticmethod
    def __is_numeric(cstr):
        return cstr.isdigit()
        # for i in range(len(cstr)):
        #     if cstr[i].isdigit():
        #         pass
        #     else:
        #         return False
        # return True

    def send_change_arena(self, arena):
        """
        allows the bot to change arenas
        although the protocal supports random arenas
        this function will only take a string
        which can be a number is pub 0 is 0
        or  it can be any arena,  # arena
        you will recicve event leaves for all player in current arena
        """
        if not arena:
            return
        # send arena leave packet
        self.queue_packet(struct.pack("<B", 0x02), reliable=True)
        self.flush_outbound_queues()
        # generate leaves for everyone in the current arena
        for p in self.players_here:
            event = GameEvent(EVENT_LEAVE)
            event.player = p
            self.__add_pending_event(event)
        # make enter arena packet
        if arena:
            if self.__is_numeric(arena):
                atype = int(arena)  # public
            else:
                atype = 0xFFFD  # private
        else:
            atype = 0xFFFF  # random arena
        packet = struct.pack("<BBHHHH", 0x01, 8, 0, 4096, 4096, atype)
        packet = packet + arena[:15] + '\x00' if atype == 0xFFFD else packet
        self.queue_packet(packet, reliable=True)

        event = GameEvent(EVENT_ARENA_CHANGE)
        event.old_arena = self.arena
        self.arena = arena
        self.__add_pending_event(event)

    def send_ship_change(self, ship_type):
        """Sends a ship change request to the server.

        Note that until you receive an EVENT_CHANGE update for the bot,
        your ship has not changed."""

        packet = struct.pack("<BB", 0x18, ship_type)
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_pickup_flags(self, flag_id):
        """
        try to pickup a flag
        """
        packet = struct.pack("<BH", 0x13, flag_id)
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_flag_drop(self):
        """
        if the bot is carrying flags sending this command will
        make it drop all flags at its current coordinates
         """
        packet = struct.pack("<B", 0x15)
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_pickup_ball(self, ball_id):
        """
        try to pickup a Ball - id is the ball id
        """
        if 0 <= ball_id < MAX_BALLS:
            b = self.ball_list[ball_id]
            packet = struct.pack("<BBI", 0x20, b.id, b.time)
            self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_score_goal(self, bid):  # doesnt work
        """
        try to score a goal if the bot has a ball
        """
        # if id = 0 and id <MAX_BALLS:
        #    b = self.ball_list[bid]
        packet = struct.pack("<BBI", 0x21, bid, get_tick_count_hs())
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_shoot_ball(self, bid, x, y, dx, dy):
        """shoots powerball if the bot has a ball x, y in pixels"""
        # if id = 0 and id <MAX_BALLS:
        #    b = self.ball_list[bid]
        packet = struct.pack("<BBhhhhhI", 0x1F, bid, x, y,
                             dx, dy, self.pid, get_tick_count_hs())
        self.queue_packet(packet, reliable=True, priority=PRIORITY_HIGH)

    def send_attach(self, pp):  # untested
        """send_attach use this if you want the bot to attach to a player"""
        pid = self.__to_pid(pp)
        packet = struct.pack("<BH", 0x10, pid)
        self.queue_packet(packet, reliable=True)

    def send_change_settings(self, settings_list):
        """
        send_change_settings:allows you to cluster
        and send a list of settings changes in one packet
        settings_list must be a list 1 or more items
        eg. send_change_settings(["Team:MaxPerTeam:4",
                "Team:MaxPerPrivateTeam:4"])
        """
        if isinstance(settings_list, list) and len(settings_list) > 0:
            packet = struct.pack("<B", 0x1d)
            for e in settings_list:
                packet += e + chr(0)
            packet += chr(0)
            self.queue_packet(packet, reliable=True)
        else:
            self.__log(
                DEBUG,
                ("sendChangesettings argument must be a list of strings with "
                 "atleast 1 entry")
            )

    @staticmethod
    def __parse_extra_player_data(event, packet):
        energy, s2c_ping, timer, t1 = struct.unpack_from("<HHHI", packet)
        event.sd_updated = True
        player = event.player
        player.sd_energy = energy
        player.sd_s2c_ping = s2c_ping
        player.sd_timer = timer
        player.sd_shields = 1 if t1 & 1 else 0
        player.sd_super = 1 if (t1 & (1 << 1)) else 0
        player.sd_bursts = (t1 & (0xF << 2)) >> 2
        player.sd_repels = (t1 & (0xF << 6)) >> 6
        player.sd_thors = (t1 & (0xF << 10)) >> 10
        player.sd_bricks = (t1 & (0xF << 14)) >> 14
        player.sd_decoys = (t1 & (0xF << 18)) >> 18
        player.sd_rockets = (t1 & (0xF << 22)) >> 22
        player.sd_portals = (t1 & (0xF << 26)) >> 26
        player.sd_time = get_tick_count_hs()

    def __handle_small_position_update_packet(self, packet):
        # pos updates dont come for yourself, so this packet does not
        # check against the bot's pid
        ptype, rotation, timestamp, x_pos, latency, bounty, pid, status, \
            y_vel, y_pos, x_vel = struct.unpack_from("<BBHHBBBBhHh", packet)
        player = self.find_player_by_pid(pid)
        if player:
            player.rotation = rotation
            player.x_pos = x_pos
            player.y_pos = y_pos
            player.x_vel = x_vel
            player.y_vel = y_vel
            player.set_status(status)
            player.bounty = bounty
            player.ping = latency
            player.last_pos_update_tick = get_tick_count_hs()

            event = GameEvent(EVENT_POSITION_UPDATE)
            event.player = player
            event.fired_weapons = False
            if len(packet) == 26:
                self.__parse_extra_player_data(event, packet[16:])
            else:
                event.sd_updated = False

            self.__add_pending_event(event)

    def __handle_koth_game_reset(self, packet):
        # dont really need to decode this just
        # send a response to remove bot from koth game
        self.queue_packet(struct.pack("<B", 0x1E), reliable=True)

    @staticmethod
    def __parse_weapons(event, weapons):
        event.weapons_type = (weapons & 0x1F)
        event.weapons_level = (weapons & (0x3 << 4)) >> 4
        event.shrap_bouncing = (weapons & (1 << 6)) >> 6
        event.shrap_level = (weapons & (0x3 << 7)) >> 7
        event.shrap = (weapons & (0x1F << 9)) >> 9
        event.alternate = 1 if (1 << 15 & weapons) else 0

    def __handle_large_position_update_packet(self, packet):
        # pos updates dont come for yourself, so this packet does not
        # check against the bot's pid
        # xxx this packet is actually a lot larger and some fields are
        # ignored here
        ptype, rotation, timestamp, x_pos, y_vel, pid, x_vel, checksum, \
            status, latency, y_pos, bounty, weapons = \
            struct.unpack_from("<BBHHhHhBBBHHH", packet)

        player = self.find_player_by_pid(pid)
        if player:
            player.rotation = rotation
            player.x_pos = x_pos
            player.y_pos = y_pos
            player.x_vel = x_vel
            player.y_vel = y_vel
            player.set_status(status)
            player.bounty = bounty
            player.ping = latency
            player.last_pos_update_tick = get_tick_count_hs()

            event = GameEvent(EVENT_POSITION_UPDATE)
            event.player = player
            # parse weapons
            event.fired_weapons = True
            self.__parse_weapons(event, weapons)
            # parse extra data if it exists
            if len(packet) == 31:
                self.__parse_extra_player_data(event, packet[21:])
            else:
                event.sd_updated = False
            self.__add_pending_event(event)

    def __handle_kill_packet(self, packet):
        ptype, death_green_id, killer_pid, killed_pid, bounty, \
            flags_transfered = struct.unpack_from("<BBHHHH", packet)

        killer = self.find_player_by_pid(killer_pid)
        killed = self.find_player_by_pid(killed_pid)

        if killer and killed:
            event = GameEvent(EVENT_KILL)
            event.killed = killed
            event.killer = killer
            event.death_green_id = death_green_id
            event.bounty = bounty
            event.flags_transfered = flags_transfered
            killer.flag_count += flags_transfered
            killed.flag_count = 0
            self.__add_pending_event(event)

    def __event_kill_postprocessor(self, event):
        pass

    def __handle_arena_list_packet(self, packet):
        """'arenaname\x00\xFF\xFF'"""
        offset = 1  # skip the type byte
        arena_list = []
        while offset < len(packet):
            terminating_null = packet.find('\x00', offset)
            name = packet[offset:terminating_null]
            offset = terminating_null + 1
            count, = struct.unpack_from("h", packet, offset)
            offset += 2
            arena_list.append((name, count))

        event = GameEvent(EVENT_ARENA_LIST)
        event.arena_list = arena_list
        self.__add_pending_event(event)

    def __handle_brick_drop_packet(self, packet):
        packet = packet[1:]
        l = []
        while len(packet) >= 16:
            x1, y1, x2, y2, freq, bid, timestamp = \
                struct.unpack_from("HHHHHHI", packet)
            l.append(Brick(x1, y1, x2, y2, freq, bid, timestamp))
            packet = packet[16:]
        event = GameEvent(EVENT_BRICK)
        event.brick_list = l
        self.__add_pending_event(event)

    def __handle_warpto_packet(self, packet):
        ptype, x, y = struct.unpack_from("<BHH", packet)
        self.x_pos = x << 4
        self.y_pos = y << 4
        self.__queue_position_update_packet()

    def __handle_compressed_map_packet(self, packet):  # untested
        ptype, mapname = struct.unpack_from("<B16s", packet)
        mapdata = zlib.decompress(packet[17:])
        mapname = mapname[0:mapname.find(chr(0))]
        f = open(mapname, "wb")
        f.write(mapdata)
        f.close()
        self.__log(DEBUG, "downloaded " + mapname)

    def __handle_file_transfer(self, packet):
        ptype, filename = struct.unpack_from("<B16s", packet)
        if len(packet) == 17:
            self.__log(ERROR, "Requested File Doesnt Exist: " + filename)
        else:
            if filename[0] == chr(0):
                filename = "news.txt"
                data = packet[17:]
            else:
                filename = filename[0:filename.find(chr(0))]
                data = packet[17:]
                # data = zlib.decompress(packet[17:])

            f = open(filename, "wb")
            f.write(data)
            f.close()
            self.__log(DEBUG, "downloaded " + filename)
        # self.__log(INFO, "*getfile disabled")

    def __handle_request_file(self, packet):  # 0x19
        ptype, lfname, rfname = struct.unpack_from("<B256s16s", packet)
        lfname = lfname[0:lfname.find(chr(0))]
        rfname = rfname[0:rfname.find(chr(0))]
        self.__log(DEBUG, "server is requesting %s as %s" % (lfname, rfname))
        self.__send_file(lfname, rfname)

    def __send_file(self, filename, remotefilename):  # 0x16
        if os.path.isfile(os.getcwd() + "//" + filename):
            packet = struct.pack("<B16s", 0x16, remotefilename[0:14]+chr(0))
            # packet+= zlib.compress(open(os.getcwd()+
            #   "//" + filename, "rb").read())
            packet += open(os.getcwd() + "//" + filename, "rb").read()
            self.__log(DEBUG, "sending file:%s" % filename)
            self.queue_packet(packet)
        else:
            self.__log(ERROR, "sendfile %s localfile doesnt exist" % filename)
        # self.__log(INFO, "*putfile disabled(doesnt work)")

    def __request_level_file(self):
        self.queue_packet(struct.pack("<B", 0x0C), reliable=True)

    def __handle_map_information_packet(self, packet):
        ptype, mapname, checksum_remote = struct.unpack_from("<B16sI", packet)
        if self.__downloadLevelFiles:
            mapname = mapname[0:mapname.find(chr(0))]
            if os.path.isfile(os.getcwd() + "//" + mapname):
                checksum_local = self.fc.get_file_checksum(mapname)
                if checksum_local != checksum_remote:
                    # self.__request_level_file()
                    # self.__log(DEBUG, "MAPLEVEL CHANGED???: ([%x]!=%x" %
                    #   (checksum_local, checksum_remote))
                    pass
            else:
                self.__request_level_file()

    def put_file(self, filename):  # doesnt work dont use!!!
        self.send_public_message("*putfile " + filename, sound=SOUND_NONE)

    def get_file(self, filename):
        self.send_public_message("*getfile " + filename, sound=SOUND_NONE)

    def __handle_watch_damage_packet(self, packet):
        ptype, attacked, time_stamp = struct.unpack_from("<BHI", packet)
        packet = packet[7:]
        pattacked = self.find_player_by_pid(attacked)
        while len(packet) >= 9:
            attacker, weapons, energy_old, energy_lost = struct.unpack_from(
                "<HHHH", packet)
            event = GameEvent(EVENT_WATCH_DAMAGE)
            event.attacked = pattacked
            event.attacker = self.find_player_by_pid(attacker)
            event.energy_old = energy_old
            event.energy_lost = energy_lost
            self.__parse_weapons(event, weapons)
            self.__add_pending_event(event)
            packet = packet[9:]
            # print("damage " + event.attacked.name +" damage:" + str(
            #   event.energy_lost) + " old:" + str(event.energy_old) +
            #   " from " + event.attacker.name)

    @staticmethod
    def __make_padded_string(data, size):
        return str(data).rjust(size, chr(0))
        # d = data + ((size - len(data)) * chr(0))
        # assert(len(d) == size)
        # return d

    # copied from twcore doesnt work, probably queueHugeChunkPacket broken?
    def __send_registration_form(self):
        packet = struct.pack(
            "<B32s64s32s24sBBBBBHHI40s",
            0x17,
            self.__make_padded_string("thejunky", 32),
            self.__make_padded_string("thejunky@gmail.com", 64),
            self.__make_padded_string("WTF", 32),
            self.__make_padded_string("WTF", 24),
            77, 20, 1, 1, 1, 586, 0xC000, 2036,
            self.__make_padded_string(self.name, 40)
        )
        packet += (self.__make_padded_string("PYCore", 40) * 14)

        self.queue_packet(packet, True, PRIORITY_HIGH)

    def reset_state(self):
        if self.__connected:
            raise Exception("wtf you cant reset state while connected you fag")
        else:
            CoreStack.reset_state(self)
            self.__players_by_pid = {}  # pid: Player
            self.__players_by_name = {}  # name: Player

            self.__event_list = []
            self.players_here = []
            self.__players_by_name = {}
            self.__players_by_pid = {}

            self.__last_event_generated = None
            self.__timer_list = []  # Timer()
            self.__next_timer_id = 0
            self.__last_timer_expire_tick = get_tick_count_hs()

    def wait_for_event(self):
        """Wait for an event.

        A GameEvent class instance is returned, and its type can be
        found in GameEvent.type. The type will be one of EVENT_Xxx.
        If the bot is disconnected None will be returned."""

        # give the core the chance to post process the last event generated
        if self.__last_event_generated is not None:
            postprocessor = self.__event_postprocessors.get(
                self.__last_event_generated.type)
            if postprocessor is not None:
                postprocessor(self.__last_event_generated)
            self.__last_event_generated = None

        if self.__connected is False:
            return None

        # xxx make sure large event lists dont starve the core, and
        # i/o should probably be done between events...
        while True:
            if len(self.__event_list) > 0:
                # give the core the chance to preprocess events, this is needed
                # because if the changes were made immediately when the event
                # was received (as opposed to when the packet is removed from
                # queue for processing)
                # the core's view of the game state might be incorrect
                event = self.__event_list.pop(0)
                preprocessor = self.__event_preprocessors.get(event.type)
                if preprocessor is not None:
                    event = preprocessor(event)
                if event is None:
                    continue
                self.__last_event_generated = event
                return event

            # there are no more bot-level events to process, so call the core's
            # own wait for event handler
            event = CoreStack.wait_for_event(self)
            if event.type == core_stack.EVENT_GAME_PACKET_RECEIVED:
                try:
                    game_type, = struct.unpack_from("<B", event.packet)
                    handler = self.__packet_handlers.get(game_type)
                    if handler is not None:
                        handler(event.packet)
                        if self.__debug:
                            self.__log(
                                DEBUG,
                                "Handler for Type: 0x%02X is %s" % (
                                    game_type, handler)
                            )

                except (IndexError, struct.error):
                    if game_type:
                        self.__log(
                            CRITICAL,
                            ('Structure error in SubspaceBot packet'
                             ' handler: %02X') % game_type
                        )
                        self.__log(CRITICAL, event.packet.encode('hex'))
                        self.__log(CRITICAL, sys.exc_info())
                        formatted_lines = traceback.format_exc().splitlines()
                        for l in formatted_lines:
                            self.__log(CRITICAL, l)

            # map core stack events to game stack events
            elif event.type == core_stack.EVENT_TICK:
                self.__add_pending_event(GameEvent(EVENT_TICK))
            elif event.type == core_stack.EVENT_DISCONNECT:
                self.__add_pending_event(GameEvent(EVENT_DISCONNECT))

    def __add_pending_event(self, game_event):
        self.__event_list.append(game_event)
