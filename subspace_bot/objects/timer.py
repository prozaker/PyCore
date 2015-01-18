from subspace.core_stack import get_tick_count_hs


class Timer:
    """Represents a timer created with set_timer in the core."""

    id = None
    """The ID of the timer."""

    duration = None
    """The the duration of the timer."""

    user_data = None
    """The user_data value passed in to the set_timer() call when the
    timer was created."""

    base = None
    """The tickstamp when the timer was created."""

    def __init__(self, timer_id, seconds, user_data=None):
        self.id = timer_id
        self.duration = seconds * 100  # to ticks
        self.user_data = user_data
        self.base = get_tick_count_hs()
