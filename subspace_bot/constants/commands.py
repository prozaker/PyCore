COMMAND_TYPE_PUBLIC = 0x02
"""A public COMMAND (blue)."""

COMMAND_TYPE_TEAM = 0x03
"""A team COMMAND (yellow)."""

COMMAND_TYPE_FREQ = 0x04
"""A freq COMMAND (green name, blue text)"""

COMMAND_TYPE_PRIVATE = 0x05
"""A private COMMAND (sourced green, in-arena)."""

COMMAND_TYPE_REMOTE = 0x07
"""A remote COMMAND (sourced green, out of arena."""

COMMAND_TYPE_CHAT = 0x09
"""A chat COMMAND (red)."""

COMMAND_TYPE_ALERT = 0x0A
"""Actually a remote message but lets pass it on as an alert"""

# convenience vars for command registration
COMMAND_LIST_PP = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_PRIVATE]
"""private and public COMMAND"""

COMMAND_LIST_PR = [COMMAND_TYPE_PRIVATE, COMMAND_TYPE_REMOTE]
"""private and public COMMAND"""

COMMAND_LIST_PPR = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_PRIVATE,
                    COMMAND_TYPE_REMOTE]
"""private and public and remote COMMAND"""

COMMAND_LIST_PPRC = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_PRIVATE,
                     COMMAND_TYPE_REMOTE, COMMAND_TYPE_CHAT]
"""private and public and remote and Chat COMMANDs"""

COMMAND_LIST_PPC = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_PRIVATE,
                    COMMAND_TYPE_REMOTE, COMMAND_TYPE_CHAT]
"""private and public and Chat COMMANDs"""

COMMAND_LIST_ALL = [COMMAND_TYPE_PUBLIC, COMMAND_TYPE_TEAM,
                    COMMAND_TYPE_FREQ, COMMAND_TYPE_PRIVATE,
                    COMMAND_TYPE_REMOTE, COMMAND_TYPE_CHAT]
