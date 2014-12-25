MESSAGE_TYPE_ARENA = 0x00
MESSAGE_TYPE_SYSTEM = MESSAGE_TYPE_ARENA
"""An arena message (unsourced green)."""

MESSAGE_TYPE_PUBLIC_MACRO = 0x01
"""A public macro message (blue)."""

MESSAGE_TYPE_PUBLIC = 0x02
"""A public message (blue)."""

MESSAGE_TYPE_TEAM = 0x03
"""A team message (yellow)."""

MESSAGE_TYPE_FREQ = 0x04
"""A freq message (green name, blue text)"""

MESSAGE_TYPE_PRIVATE = 0x05
"""A private message (sourced green, in-arena)."""

MESSAGE_TYPE_WARNING = 0x06
"""A warning message from \*warn."""

MESSAGE_TYPE_REMOTE = 0x07
"""A remote message (sourced green, out of arena."""

MESSAGE_TYPE_SYSOP = 0x08
"""A sysop message (dark red)."""

MESSAGE_TYPE_CHAT = 0x09
"""A chat message (red)."""

MESSAGE_TYPE_ALERT = 0x0A
"""Actually a parsed remote message but lets pass it on as an alert"""
