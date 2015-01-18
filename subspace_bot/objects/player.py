from subspace_bot.constants.statuses import *


class Player:
    """A class that represents the a Player.  All values are read-only
    to bots except for the 'player_info' variable that is reserved for
    bot's per-player data storage.

    The x_pos, y_pos, x_vel, y_vel, and status_Xxx are only as recent as
    the last_pos_update_tick timestamp.  Position updates are only
    received for players on the bot's radar, except in the case where a
    player first enters a safe area."""

    name = None
    """The player's name"""

    squad = None
    """The player's squad"""

    banner = None
    """A player's banner"""

    pid = None
    """The player's PID, unique for all players in the arena.
    Invalid after EVENT_LEAVE."""

    ship = None
    """The player's ship, one of SHIP_Xxx.  Use GetShipName() get the
    ship's name as a string."""

    freq = None
    """The player's current frequency."""

    x_pos = None
    """The player's X coordinate, in pixels.  This is only as recent
    as 'last_pos_update_tick."""

    y_pos = None
    """The player's Y coordinate, in pixels.  This is only as recent
    as 'last_pos_update_tick."""

    x_vel = None
    """The player's X velocity.  This is only as recent
    as 'last_pos_update_tick."""

    y_vel = None
    """The player's Y velocity.  This is only as recent
    as 'last_pos_update_tick."""

    bounty = None
    """plays bounty is updated in position updats"""

    ping = None
    """also updated in event pos """

    last_pos_update_tick = None
    """The tickstamp, in hundreths of seconds, of when the player's
    last position update was received."""

    player_info = None
    """Reserved for a bot implementation's own use.  Should be set
    during EVENT_ENTER.

    For example:

    .. sourcecode:: python


        class PlayerInfo:

            def __init__(self):
                self.kill_count = 0
                self.death_count = 0

        Then in EVENT_ENTER:
            event.player.player_info = PlayerInfo()

        And in EVENT_KILL:
            event.killer.player_info.kill_count += 1
            event.killed.player_info.death_count += 1"""

    status_stealth = None
    """True if the player has stealth on, otherwise False."""

    status_cloak = None
    """True if the player has cloak on, otherwise False."""

    status_xradar = None
    """True if the player has XRadar on, otherwise False."""

    status_antiwarp = None
    """True if the player has AntiWarp on, otherwise False."""

    status_flashing = None
    """I not know what this indicates."""

    status_safezone = None
    """True if the player is in a safe area, otherwise False."""

    status_ufo = None
    """True if the player has UFO toggles, otherwise False."""
    flag_points = None
    kill_points = None
    wins = None
    losses = None

    flag_count = None
    turreted_pid = None
    # turreter_list = None

    # if carrying ball else 0xffff
    ball_id = None

    # spectator data look at sd_time to see when it was last updated
    sd_energy = None
    sd_s2c_ping = None
    sd_timer = None
    sd_shields = None
    sd_super = None
    sd_bursts = None
    sd_repels = None
    sd_thors = None
    sd_bricks = None
    sd_decoys = None
    sd_rockets = None
    sd_portals = None
    sd_time = None

    def __init__(self, name, squad, pid, ship, freq):
        """Initialize the Player object."""
        self.name = name
        self.squad = squad
        self.pid = pid
        self.ship = ship
        self.freq = freq

        self.rotation = 0
        self.x_pos = -1
        self.y_pos = -1
        self.x_vel = 0
        self.y_vel = 0
        self.last_pos_update_tick = None
        self.player_info = None
        self.set_status(0x00)

        self.flag_points = 0
        self.kill_points = 0
        self.wins = 0
        self.losses = 0

        self.flag_count = 0
        # pid of the player this player is turreting
        self.turreted_pid = 0xFFFF

        self.ping = 0
        self.bounty = 0

        # if carrying ball else 0xffff
        self.ball_id = 0xffff

        # spectator data look at sd_time to see when it was last updated
        self.sd_energy = 0
        self.sd_s2c_ping = 0
        self.sd_timer = 0
        self.sd_shields = 0
        self.sd_super = 0
        self.sd_bursts = 0
        self.sd_repels = 0
        self.sd_thors = 0
        self.sd_bricks = 0
        self.sd_decoys = 0
        self.sd_rockets = 0
        self.sd_portals = 0
        self.sd_time = 0

    def __str__(self):
        return self.name

    def set_status(self, status_flags):
        """Updates the player's status with the status flags received
        in the position update packet."""
        self.status_stealth = status_flags & STATUS_STEALTH != 0
        self.status_cloak = status_flags & STATUS_CLOAK != 0
        self.status_xradar = status_flags & STATUS_XRADAR != 0
        self.status_antiwarp = status_flags & STATUS_ANTIWARP != 0
        self.status_flashing = status_flags & STATUS_FLASHING != 0
        self.status_safezone = status_flags & STATUS_SAFEZONE != 0
        self.status_ufo = status_flags & STATUS_UFO != 0
