from logging import Handler, NOTSET
import sys
import traceback


def log_exception(logger):
    logger.error(sys.exc_info())
    formatted_lines = traceback.format_exc().splitlines()
    for l in formatted_lines:
        logger.error(l)


class LoggingChatHandler(Handler):
    """
    Logging module handler to spew entries to a specific chat
    """
    def __init__(self, level, ssbot, chat_no):
        Handler.__init__(self, level)
        self.ssbot = ssbot
        self.chat = ";" + str(chat_no) + ";"

    def emit(self, record):
        self.ssbot.send_chat_message(self.chat + self.format(record))


class LoggingTeamHandler(Handler):
    """
    Logging module handler to spew entries to a team chat
    """
    def __init__(self, level, ssbot):
        Handler.__init__(self, level)
        self.ssbot = ssbot

    def emit(self, record):
        self.ssbot.send_team_message(self.format(record))


class LoggingPublicHandler(Handler):
    """
    Logging module handler to spew entries to pub
    """
    # TODO: get rid of last arg or add it back ('prefix')
    def __init__(self, level, ssbot, _):
        Handler.__init__(self, level)

        self.ssbot = ssbot

    def emit(self, record):
        self.ssbot.send_public_message(self.format(record))


class LoggingRemoteHandler(Handler):
    """
    Logging module handler to spew entries to pub
    """
    def __init__(self, level, ssbot, name):
        Handler.__init__(self, level)
        self.ssbot = ssbot
        self.name = name

    def emit(self, record):
        self.ssbot.send_remote_message(self.name, self.format(record))


class ListHandler(Handler):
    # the logging module allows u to add handlers for log messages
    # for example maybe you want certain log entries to be added
    # to an offsite server using httppost
    # this is simple handler that i made to copy messages to a list
    # so it can be spewed to ss without reading the logfile
    # you are required to overide __init__ and emit for it to work
    def __init__(self, level=NOTSET, max_recs=100):
        Handler.__init__(self, level)
        self.list = []
        self.max_recs = max_recs
        self.max_slice = -1 * max_recs

    def emit(self, record):
        self.list.append(self.format(record))

    def load_from_file(self, filename):
        self.list = open(filename, 'r').readlines()[self.max_slice:]

    def remove_old(self):
        if len(self.list) > self.max_recs:
            self.list = self.list[self.max_slice:]

    def get_entries(self):
        return self.list[self.max_slice:]

    def clear(self):
        self.list = []


class NullHandler(Handler):
    def emit(self, record):
        pass
