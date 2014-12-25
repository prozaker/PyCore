EVENT_ERROR = 0
"""

"""

EVENT_TICK = 1
"""Occurs every 1/10th of a second.

Sets: type"""

EVENT_DISCONNECT = 2
"""Occurs when the bot disconnects from the server.

Sets: type"""

EVENT_START = 3
"""Occurs when the bot logs in to the server.

At this point, commands and messages can be sent with success.  If
the bot needs to run any commands automatically on login, this is
the time to do that.

Sets: type"""

EVENT_LOGIN = 4
"""occurs when bot is added to the playerlist so u can priv it"""

EVENT_MESSAGE = 5
"""Indicates the bot received a message.

message is the text of the message.  message_type indicates what type
of message was received, and is one of the MESSAGE_TYPE_Xxx constants.

Sets:
        event.player = player
        event.message = message
        event.message_type = message_type
        event.pname = message_name
        event.chat_no = chatnum
        event.alert_name = alert
        event.alert_arena = arena
"""

EVENT_ENTER = 6
"""Indicates a player entered the arena.

player is the player who entered.

A bot will receive an enter event for itself, so to avoid taking action
on the bot check event.player.pid against bot.pid.

Sets: type, player"""

EVENT_LEAVE = 7
"""Indicates a player left the arena.

player is the player who left.

Sets: type, player"""

EVENT_CHANGE = 8
"""Happens when a player changes ship, freq, or both.

player is the player that changed freq.  old_freq is the player's
old frequency. old_ship is the player's old ship. If {freq, ship}
didn't change, old_{ship, freq} are equal.
            event.player
            event.old_freq = player.freq
            event.old_ship = player.ship
            player.ship = new_ship
            player.freq = new_freq


"""

EVENT_COMMAND = 9
"""A command was used.

player is the player that used the command.

command is the Command object that was used.  arguments are an array,
starting at the first argument.  arguments_after is an array of an
argument and everything after it, starting at the first argument. If
there are no arguments passed, arguments and arguments_after are
empty lists.

For example after the command: !command a b c
   arguments = ['a', 'b', 'c']
   arguments_after = ['a b c', 'b c', 'c']

This allows you to match players with spaces in their name such as:
    !lag C H E E P
by using arguments_after[0]

Sets: type, player, command, arguments, arguments_after.
            event = GameEvent(EVENT_COMMAND)
            event.player = event.player
            event.command = command
            event.arguments = event.arguments
            event.arguments_after = event.arguments_after
            event.pname = event.pname
            event.plvl = event.plvl
            event.chat_no = event.chat_no
            event.alert_name = event.alert_name
            event.alert_arena = event.alert_arena
            event.command_type = event.command_type


"""

EVENT_POSITION_UPDATE = 10
"""A position update was received for player.

Sets: type, player, fired_weapons, sd_updated
updates:
            player.rotation = rotation
            player.x_pos = x_pos
            player.y_pos = y_pos
            player.x_vel = x_vel
            player.y_vel = y_vel
            player._setStatus(status)
            player.bounty = bounty
            player.ping = latency
            player.last_pos_update_tick = get_tick_count_hs()


if sd_updated == true then
spectator data in the player class is updated

if fired_weapons is true
event sets:
        event.weapons_type == WEAPON_XX
        event.weapons_level = 0-4
        event.shrap_level = 0-4?
        event.shrap = 0 -31
        event.alternate = 1 for mines if mines/proxMines else bomb/proxbomb
                          also indicates multifire/singlefire for bullets



"""

EVENT_KILL = 11
"""A kill event was set.

killer is the player who did the killing, killed is the player who died.

Sets: type, killer, killed, flags_transfered, death_green_id, bounty"""

EVENT_ARENA_LIST = 12
"""An arena list was received.  This is usually in response to
sending a pub message containing '?arena'.

arena_list is a list of (arena_name, num_players, here) tuples.

bot.arena is updated during this event.

Sets: type, arena_list"""

EVENT_TIMER = 13
"""A timer has expired.

id is the ID of the timer, returned by bot.setTimer(), of the timer
that expired. user_data is the same user_data passed to
bot.setTimer() during the timer's creation.

Timers are only granular to .1 second.

Sets: type, id, user_data"""

EVENT_GOAL = 14
"""A goal was scored.

freq is the frequency the goal was scored by.
points is the amount of points rewarded to the freq by scoring a goal.

This event has no associated PID with it.

Sets: type, freq, points"""

EVENT_FLAG_PICKUP = 15
"""Someone picked up a flag.

player is the player who picked up the flag.
flag_id is the id for the flag that was picked up.

Sets: type, player, flag_id, transferred_from"""

EVENT_FLAG_DROP = 16
"""Someone dropped a flag.

player is the player who dropped the flag.

Sets: type, player, flag_count"""

EVENT_TURRET = 17
"""A player attached to another player.

turreter is the player who attached to another player.
turreted is the player who was attached to.
old_turreted is a player if the event is a detach else it is None

Sets: type, turreter, turreted, old_turreted"""

EVENT_PERIODIC_REWARD = 18
"""Freqs are periodically given rewards for the amount of flags they own.

point_list is a list of (freq, points) tuples.

Sets: type, point_list"""

EVENT_BALL = 19
"""Ball periodically sends update packets to the server. This event
records this data.

ball_id is the ID of the ball, x and y_pos hold the x and y
coordinates in pixel-coordinates.
x and y_vel holds the x and y velocity in pixels per 10 seconds.
time might be the timestamp since last ball update packet? uncertain.

Sets: type, ball_id, x_pos, y_pos, x_vel, y_vel, player, time"""

EVENT_MODULE = 20
"""Custom module event
Sets: type, event_source, event_name, event_data
this event is so a module can share information with any other module
running on the same bot
example:
infobot will parse all the information from *info and pass the info
class as a module event to any other module that is running

"""

EVENT_BROADCAST = 21
"""Custom module event
Sets: type, bsource, bmessage
this event is used for interbot communication
think of it as equivilant to all the bots being on the
same chat sending messages to eachother
"""

EVENT_PRIZE = 22
"""
Sets time_stamp, x, y, prize, player
happens when a player picksup a green
"""

EVENT_SCORE_UPDATE = 23
"""
Sets type,
            event.player
            old values:
            event.old_flag_points
            event.old_kill_points
            event.old_wins
            event.old_losses
            new values:
            player.wins
            player.flag_points
            player.kill_points
            player.losses
            all the new values will be
player score will be updated at this time
"""

EVENT_SCORE_RESET = 24
"""
pid = 0xffff if all players reset
Sets: type, pid, player player will be None if pid is 0xffff which
indicates everyone in the arena has been reset to 0
"""

EVENT_FLAG_UPDATE = 25
"""
sets: type, freq, flag_id, x, y
this is sent periodicly, it will update the position of dropped flags
in flag drop the position of the flag wont be known until the next
flag update
"""

EVENT_FLAG_VICTORY = 26
"""
Sets:type, freq, points
"""

EVENT_ARENA_CHANGE = 27
"""
Sets type, old_arena
sent when a bot changes arenas
"""

EVENT_WATCH_DAMAGE = 28
"""
when the bot /*watchdamage's a player the bot will get this event
everytime he takes damage
event sets:
        event.attacker
        event.attacked
        event.energy_old
        event.energy_lost
        event.weapons_type == WEAPON_XX
        event.weapons_level = 1-4
        event.shrap_level = 1-4?
        event.shrap = 0 -31
        event.alternate = 1 for mines if mines/proxMines else bomb/proxbomb
"""

EVENT_BRICK = 29
"""sets  event.brick_list  where each brick is a brick class"""

EVENT_SPEED_GAME_OVER = 30
"""
sets bot_score, bot_rank, winners = [(rank, player, score), ...]
"""
