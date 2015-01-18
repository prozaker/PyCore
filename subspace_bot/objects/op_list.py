class Oplist:

    def __init__(self, filename='Ops.ini'):
        self.__ops_dict = {}
        self.__filename = filename
        self.Read()

    def __isValidLevel(self, lvl):
        return 0 < lvl <= 9

    def GetAccessLevel(self, name):
        n = name.lower()
        if n in self.__ops_dict:
            return self.__ops_dict[n]

        return 0

    def AddOp(self, lvl, name):
        n = name.lower()
        if self.__isValidLevel(lvl):
            self.__ops_dict[n] = lvl
            self.Write()
            return True

        return False

    def DelOp(self, name):
        n = name.lower()
        if n in self.__ops_dict:
            del self.__ops_dict[n]
            self.Write()
            return True

        return False

    def ListOps(self, ssbot, event):
        c = 0
        for name, lvl in self.__ops_dict.iteritems():
            if event.plvl == lvl:
                ssbot.send_reply(event, "OP:%25s:%i" % (name, lvl))
            c += 1
        if c == 0:
            ssbot.send_reply(event, "No Ops")

    def Read(self):
        self.__ops_dict = {}
        for line in open(self.__filename, 'r').readlines():
            line = line.strip().lower()
            if line.strip() != "":
                lvl = int(line[0])
                name = line[2:]
                self.__ops_dict[name] = lvl
        return True

    def Write(self):
        file = open(self.__filename, 'w')
        for name, lvl in self.__ops_dict.iteritems():
            file.write(str(lvl) + ":" + name + "\n")
