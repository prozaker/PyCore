import logging
import sys
import os

from subspace_bot.constants.ships import SHIP_NAMES
from subspace_bot.objects.bot import SubspaceBot
from subspace_bot.utilities.loggers import log_exception
from subspace_bot.utilities.module import ModuleData


def get_ship_name(ship):
    """Get the name of a ship from a SHIP_Xxx constant."""
    try:
        return SHIP_NAMES[ship]
    except KeyError:
        return 'Unknown'


def bot_main(bot_class, debug=False, is_master=False, arena="#python"):
    """Use this method to test bots during development (to run bots
    in stand-alone mode)
    """
    from Credentials import botowner, botname, botpassword
    try:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        # set a format
        str_format = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        formatter = logging.Formatter(str_format)

        # define a Handler which writes INFO messages or higher
        # to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the mainloop logger
        logger.addHandler(console)

        filehandler = logging.FileHandler(
            os.getcwd() + R"/" + __name__ + ".log", mode='a')
        filehandler.setLevel(logging.ERROR)
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)

        ssbot = SubspaceBot(
            debug, is_master, None, logging.getLogger(__name__ + ".Core"))
        ssbot.set_bot_info(__name__, "TestBoT", botowner)

        # get the module object for the current file...
        module = sys.modules[globals()['__name__']]
        md = ModuleData("TesttBot", module, "None", "test.ini", "",
                        logging.getLogger(__name__))
        bot = bot_class(ssbot, md)

        ssbot.connect_to_server(
            '66.36.247.83', 7900, botname, botpassword, arena)

        while ssbot.is_connected():
            event = ssbot.wait_for_event()
            bot.handle_events(ssbot, event)
    except Exception as e:
        log_exception(logger)
        raise e
    finally:
        bot.cleanup()
        logger.critical("Testbot shutting down")
        filehandler.close()
