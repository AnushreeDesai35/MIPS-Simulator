class RegisterData:
    def __init__(self, register_file):
        self.regs = []
        with open(register_file) as register_data:
            for index, line in enumerate(register_data):
                self.regs[index+1].append(int(line))