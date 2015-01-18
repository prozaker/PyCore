import twitter

from subspace_bot.interface import BotInterface
from subspace_bot.constants.commands import *
from subspace_bot.constants.events import *

class Bot(BotInterface):
    def __init__(self, bot, md):
        BotInterface.__init__(self, bot, md)
        bot.register_module_info(
            __name__,
            "TweetBot",
            "The Junky",
            "updates status on twitter",
            ".01"
        )
        self._api = twitter.Api(username='extreme_games', password=self.param)
        self._tweet_command_id = bot.register_command(
            '!tweet',
            "!tw",
            0,
            COMMAND_LIST_ALL,
            "web",
            "[message]",
            'update status on twitter.com/extreme_games'
        )

    def handle_events(self, bot, event):
        if event.type == EVENT_COMMAND and \
                event.command.id == self._tweet_command_id:
            if self.oplist.GetAccessLevel(event.player.name) > 0:
                if len(event.arguments) > 0 and \
                        len(event.arguments_after[0]) < 140:
                    status = self._api.PostUpdate("%s - %s" % (
                        event.arguments_after[0], event.player.name))
                    bot.send_arena_message(
                        "%s just posted: %s on twitter" % (
                            status.user.name, status.text)
                    )
                else:
                    bot.send_private_message(
                        event.player.name,
                        "you must provide a message of 1 to 140 characters"
                    )
            else:
                bot.send_private_message(event.player.name, "access denied")

    def cleanup(self):
        pass
