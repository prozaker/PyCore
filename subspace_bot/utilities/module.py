import sys
import os

from subspace_bot.utilities.loggers import log_exception
from subspace_bot.interface import BotInterface


class ModuleData():
    """
    Added moduledata to facilitate adding features to modules in the
    future without breaking the interface
    """
    def __init__(self, module_name, module, param, inifile, args, logger):
        self.module_name = module_name
        self.module = module
        self.param = param
        self.inifile = inifile
        self.logger = logger
        self.module_path = os.path.dirname(self.module.__file__)
        self.args = args


# this is fugly and might cause problems when the module is loaded multiple
# times but should work for development at least
def load_module(name):
    # TODO: improve method/module handling
    # if module is already loaded
    if name in sys.modules:
        # unload module
        del sys.modules[name]
    # reload module
    module = __import__(name, globals=globals(), locals=locals(),
                        fromlist=["*"])
    # module = importlib.import_module(name)
    return module


def load_bot(ssbot, modulename, param, inifile, args, logger):
    bot = None
    try:
        module = load_module(modulename)
        if issubclass(module.Bot, BotInterface):
            md = ModuleData(modulename, module, param, inifile, args, logger)
            bot = module.Bot(ssbot, md)
        else:
            msg = (
                "%s.Bot() is not a subclass of BotInterface, "
                "and can't be loaded"
            )
            logger.error(msg % modulename)
            bot = None
    except:
            msg = "Trying to instantiate %s caused Exception"
            logger.error(msg % modulename)
            log_exception(logger)
            bot = None
    finally:
        return bot
