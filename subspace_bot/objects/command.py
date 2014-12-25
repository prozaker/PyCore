class Command():

    def __init__(self, id, name, alias, access_level, msg_types_list,
                 category, args, help_short, help_long=None):
        self.id = id
        self.name = name
        self.alias = alias
        self.access_level = access_level
        self.msg_types = msg_types_list
        self.category = category
        self.args = args
        self.help_short = help_short
        self.help_long = help_long

    def is_allowed(self, ss_msg_type):
        return ss_msg_type in self.msg_types
