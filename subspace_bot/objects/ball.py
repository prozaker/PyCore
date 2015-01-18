class Ball():

    def __init__(self, ball_id, pid=0xFFFF, x=0xFFFF, y=0xFFFF):
        self.id = ball_id
        self.pid = pid
        self.x = x
        self.y = y
        self.time = 0
