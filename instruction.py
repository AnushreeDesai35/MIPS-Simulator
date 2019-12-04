from constants import *
class Instruction:
    def __init__(self, name, destination_register=None, source_register1=None, source_register2=None, processing_units = []):
        self.name = name.split(',')[0].upper()
        self.destination_register = destination_register.split(',')[0] if(destination_register != None) else None
        self.source_register1 = source_register1.split(',')[0].upper() if(source_register1 != None) else None
        self.source_register2 = source_register2.split(',')[0].upper() if(source_register2 != None) else None
        self.i_type = ""
        if self.name in DATA_TRANSFER:
            self.i_type = DATA_TRANSFER
        elif self.name in ARITHMETIC_LOGICAL:
            self.i_type = ARITHMETIC_LOGICAL
        elif self.name in CONTROL:
            self.i_type = CONTROL
        else:
            self.i_type = SPECIAL
        self.current_stage = 0
        self.completed_on = {
            IF: None,
            ID: None,
            EX: None,
            MEM: None,
            WB: None
        }
        self.finished = False
        self.unit = self.find_inst_unit(processing_units)
        self.execution_cycles = self.calculate_execution_cycles(processing_units)
        self.memory_cycles = self.calculate_memory_cycles(processing_units)

    def find_inst_unit(self, processing_units):
        for f_unit, instructions in UNIT_INST_MAP.items():
            if(self.name in instructions):
                return list(filter(lambda pu: pu.name == f_unit, processing_units))[0]
            elif(self.name in DATA_TRANSFER):
                return list(filter(lambda pu: pu.name == INT_AL, processing_units))[0]

    def calculate_memory_cycles(self, processing_units):
        if(self.name in [LOAD_DOUBLE, STORE_DOUBLE]):
            return 2
        elif(self.name in UNIT_INST_MAP[INT_AL]):
            return 1
        elif(self.name in [LOAD, STORE]):
            return 1
        else: return 0

    def calculate_execution_cycles(self, processing_units):
        if(self.name in UNIT_INST_MAP[FP_ADDER]):
            return int(list(filter(lambda pu: pu.name == FP_ADDER, processing_units))[0].cycle_count)
        elif(self.name in UNIT_INST_MAP[FP_MULTIPLIER]):
            return int(list(filter(lambda pu: pu.name == FP_MULTIPLIER, processing_units))[0].cycle_count)
        elif(self.name in UNIT_INST_MAP[FP_DIVIDER]):
            return int(list(filter(lambda pu: pu.name == FP_DIVIDER, processing_units))[0].cycle_count)
        else: return 1
        
    def __str__(self):
        return str(self.name) + " " + str(self.destination_register) + " " + str(self.source_register1) + " " + str(self.source_register2)

    def next_stage_proceed_check(self, stages_busy_status, dependency_dict):
        proceed = False
        issued = self.current_stage == 0
        raw = self.check_RAW(self.source_register1, self.source_register2, dependency_dict)
        if raw: return False, issued

        if not self.finished:
            if self.current_stage == ID:
                if self.name in CONTROL + SPECIAL:
                    proceed = True
                else:
                    notbusy = self.unit.pipelined == "YES" or not self.unit.busy
                    proceed = notbusy
            elif(self.current_stage == EX):
                if(self.execution_cycles > 0 ): self.execution_cycles -= 1
                if(self.execution_cycles == 0): proceed = not stages_busy_status[self.current_stage + 1] if self.name in UNIT_INST_MAP[INT_AL] + DATA_TRANSFER else not stages_busy_status[self.current_stage + 2]
                else: proceed = False
            else:
                proceed = not stages_busy_status[self.current_stage + 1]
        return proceed, issued

    def check_RAW(self, source_register1, source_register2, dependency_dict):
        if self.current_stage == ID:
            sr1_check = source_register1 in dependency_dict and dependency_dict[source_register1] != None
            sr2_check = source_register2 in dependency_dict and dependency_dict[source_register2] != None
            return sr1_check or sr2_check
        else: return False

    def proceed_to_next_stage(self, stages_busy_status, clock_cycle, dependency_dict):
        if(self.current_stage == 0):
            self.current_stage += 1
            stages_busy_status[IF] = True
        elif(self.current_stage == IF):
            self.current_stage += 1
            stages_busy_status[IF] = False
            stages_busy_status[ID] = True
            self.completed_on[IF] = clock_cycle
        elif(self.current_stage == ID):
            if(self.name in CONTROL + SPECIAL):
                self.current_stage = 6
                stages_busy_status[ID] = False
                self.completed_on[ID] = clock_cycle
                self.finished = True
            else:
                self.unit.busy = True
                self.current_stage += 1
                stages_busy_status[ID] = False
                self.completed_on[ID] = clock_cycle
                dependency_dict[self.destination_register] = self
        elif(self.current_stage == EX):
            if(self.unit.pipelined == "YES"):
                self.unit.busy = False
            else:
                self.unit.busy = True
            if(self.execution_cycles == 0):
                self.unit.busy = False
                self.completed_on[EX] = clock_cycle
                if(self.name in (UNIT_INST_MAP[INT_AL]) + (DATA_TRANSFER)):
                    self.current_stage += 1
                    stages_busy_status[MEM] = True
                else:
                    self.current_stage += 2
                    stages_busy_status[WB] = True

        elif(self.current_stage == MEM):
            self.memory_cycles -= 1
            if(self.memory_cycles == 0):
                self.current_stage += 1
                stages_busy_status[MEM] = False
                self.completed_on[MEM] = clock_cycle
                stages_busy_status[WB] = True

        elif(self.current_stage == WB):
            self.completed_on[WB] = clock_cycle
            self.finished = True
            stages_busy_status[WB] = False
            dependency_dict[self.destination_register] = None
