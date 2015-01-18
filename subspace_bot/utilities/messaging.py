from subspace_bot.constants.messages import MESSAGE_TYPE_PUBLIC, \
    MESSAGE_TYPE_PRIVATE, MESSAGE_TYPE_REMOTE, MESSAGE_TYPE_TEAM, \
    MESSAGE_TYPE_FREQ, MESSAGE_TYPE_CHAT
from subspace_bot.constants.other import SOUND_NONE
from subspace_bot.objects.player import Player


class SSmessengerException(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class SSmessenger():
    """
    This class is used  if you want to use differing methods to print/message
    in Subspace. for example Database results can be printed to
    team/freq/pub/chat/remote
    supports
        MESSAGE_TYPE_PUBLIC,
        MESSAGE_TYPE_PRIVATE,MESSAGE_TYPE_REMOTE (target must be a name)
        MESSAGE_TYPE_TEAM,
        MESSAGE_TYPE_FREQ (target must be an freq)
        MESSAGE_TYPE_CHAT (target must be a chat channel)

        for arena or zone or *bot messages use MESSAGE_TYPE_PUBLIC with
        the appropriate prefix

        throws SSmessengerException on error
    """
    def __init__(self, ssbot, mtype, target=None, prefix=""):
        self.ssbot = ssbot
        self.func = None
        self.target = None
        self.prefix = prefix
        if mtype == MESSAGE_TYPE_PUBLIC:
            self.func = self.__pub
        elif mtype == MESSAGE_TYPE_PRIVATE:
            if isinstance(target, str):
                self.player = ssbot.find_player_by_name(target)
                if not self.player:
                    raise SSmessengerException("Player NotFound")
            elif isinstance(Player, target):
                self.player = target
            else:
                raise SSmessengerException((
                    "MessageType private/remote but target isn't "
                    "a string/player"))
            self.func = self.__priv
        elif mtype == MESSAGE_TYPE_REMOTE:
            if isinstance(target, str):
                self.func = self.__rmt
                self.playername = target
            else:
                raise SSmessengerException(
                    "MessageType remote but target is'nt a string")
        elif mtype == MESSAGE_TYPE_TEAM:
            self.func = self.__team
        elif mtype == MESSAGE_TYPE_FREQ:
            if isinstance(target, int):
                raise SSmessengerException(
                    "MessageType freq but target is'nt a freq")
            self.func = self.__freq
            self.freq = target
        elif mtype == MESSAGE_TYPE_CHAT:
            if isinstance(target, int):
                raise SSmessengerException(
                    "MessageType chat but target is'nt a channel")
            self.func = self.__chat
            self.chat = ";"+str(target)+";"
        else:
            raise SSmessengerException("MessageType not supported")

    def __pub(self, message, sound=SOUND_NONE):
        self.ssbot.send_public_message(message, sound)

    def __priv(self, message, sound=SOUND_NONE):
        self.ssbot.send_private_message(self.player, message, sound)

    def __rmt(self, message, sound=SOUND_NONE):
        self.ssbot.send_remote_message(self.playername, message, sound)

    def __team(self, message, sound=SOUND_NONE):
        self.ssbot.send_team_message(message, sound)

    def __freq(self, message, sound=SOUND_NONE):
        self.ssbot.send_freq_message(self.freq, message, sound)

    def __chat(self, message, sound=SOUND_NONE):
        self.ssbot.send_chat_message(self.chat + message, sound)

    def send_message(self, message, sound=SOUND_NONE):
        self.func(self.prefix + message, sound)
