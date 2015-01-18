class BotInterface:
    # TODO: remove bot param from constructor signature

    def __init__(self, bot, md):
        self.md = md
        # param defined in config, could be any string
        self.param = md.param
        self.inifile = md.inifile

        # logging module allows modules log to !log,console,and file
        self.logger = md.logger

        # when modules are dynamicly loaded
        # i dont think the rest of the file is easy/possible?
        # to add to the current context, even if it was possible
        # i assume it will cause some sort of name Mangling
        # i assume we can get all the variables we need if
        # i pass the module i get from __import__ to the botclass
        # so if u need you specific Playerinfo for example u
        # can get to it by doing module.playerinfo
        self.module_name = md.module_name
        self.module = md.module
        self.module_path = md.module_path
        self.args = md.args  # any arguments passed by !sb this is a string

    def handle_events(self, ssbot, event):
        raise NotImplementedError(
            'Method handle_events must be overriden in the child class'
        )

    def cleanup(self):
        pass
