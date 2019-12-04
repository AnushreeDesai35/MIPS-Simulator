class ProcessingUnit:
    def __init__(self, name, cycle_count, pipelined=None, busy=None):
        self.name = name.split(':')[0].upper()
        self.cycle_count = (str(cycle_count).split(',')[0]) if(cycle_count != None) else None
        self.pipelined = pipelined.split(',')[0].upper() if(pipelined != None) else "NO"
        self.busy = False

    def __str__(self):
        return str(self.name) + " " + str(self.cycle_count) + " " + str(self.pipelined)
