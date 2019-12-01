from constants import *
class Instruction:
    def __init__(self, name, destination_register=None, source_register1=None, source_register2=None, processing_units = []):
        self.name = name.split(',')[0]
        self.destination_register = destination_register.split(',')[0] if(destination_register != None) else None
        self.source_register1 = source_register1.split(',')[0] if(source_register1 != None) else None
        self.source_register2 = source_register2.split(',')[0] if(source_register2 != None) else None
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
        self.current_stage_remaining_cycle = None
        self.completed_on = {
            IF: None,
            ID: None,
            EX: None,
            WB: None,
        }
        self.finished = False
        self.execution_cycles = self.calculate_execution_cycles(processing_units)

    def calculate_execution_cycles(self, processing_units):
        # if(self.name in [HALT, UNCONDITIONAL_JUMP, BRANCH_EQUAL, BRANCH_NOT_EQUAL]):
        #     return 0
        # elif(self.name in [DADD, DADDI, DSUB, DSUBI, AND, ANDI, OR, ORI]):
        #     return 3
        # elif(self.name in [LOAD, LOAD_DOUBLE, STORE_DOUBLE, STORE_DOUBLE]):
        #     return 3
        if(self.name in [ADD_DOUBLE, SUBTRACT_DOUBLE]):
            return int(list(filter(lambda pu: pu.name == FP_ADDER, processing_units))[0].cycle_count)
        elif(self.name in [MULTIPLY_DOUBLE]):
            return int(list(filter(lambda pu: pu.name == FP_MULTIPLIER, processing_units))[0].cycle_count)
        elif(self.name in [DIVIDE_DOUBLE]):
            return int(list(filter(lambda pu: pu.name == FP_DIVIDER, processing_units))[0].cycle_count)
        else: return 1
        
    def __str__(self):
        return str(self.name) + " " + str(self.destination_register) + " " + str(self.source_register1) + " " + str(self.source_register2)

    def next_stage_proceed_check(self, stages_busy_status, clock_cycle):
        proceed = False
        issued = False
        if not self.finished and not stages_busy_status[self.current_stage + 1]:
            if self.current_stage == 0:
                issued = True
            proceed = True
        return proceed, issued

    def proceed_to_next_stage(self, stages_busy_status, clock_cycle):
        # self.current_stage += 1
        # stages_busy_status[self.current_stage] = False
        # stages_busy_status[self.current_stage + 1] = True
        # self.completed_on[self.current_stage] = clock_cycle
        if(self.current_stage == 0):
            self.current_stage += 1
            stages_busy_status[IF] = True
        elif(self.current_stage == IF):
            self.current_stage += 1
            stages_busy_status[IF] = False
            stages_busy_status[ID] = True
            self.completed_on[IF] = clock_cycle
        elif(self.current_stage == ID):
            self.current_stage += 1
            stages_busy_status[ID] = False
            stages_busy_status[EX] = True
            self.completed_on[ID] = clock_cycle
        elif(self.current_stage == EX):
            self.execution_cycles -= 1
            if(self.execution_cycles == 0):
                self.current_stage += 1
                stages_busy_status[EX] = False
                self.completed_on[EX] = clock_cycle
        elif(self.current_stage == WB):
            self.completed_on[WB] = clock_cycle
            self.finished = True
            
    # def execute_data_tranfer_instruction(self):
    #     print(self.destination_register)
    #     print(self.source_register1)
    # def execute_arithmetic_logical_instruction(self):
    #     print(self.destination_register)
    #     print(self.source_register1)
    #     print(self.source_register2)
    # def execute_control_instruction(self):
    #     print(self.destination_register)
    #     print(self.source_register1)
    #     print(self.source_register2)
    # def execute_special_instruction(self):
    #     print(self.destination_register)
    #     print(self.source_register1)

    # def execute_instruction(self, processing_units):
    #     processing_units.busy = True
    #     processing_units.setBusy(True)

    #     if self.name in DATA_TRANSFER:
    #         self.execute_data_tranfer_instruction()
    #     elif self.name in ARITHMETIC_LOGICAL:
    #         self.execute_arithmetic_logical_instruction()
    #     elif self.name in CONTROL:  
    #         self.execute_control_instruction()
    #     else:
    #         self.execute_special_instruction()

    # def fetch_instruction(self, stages_busy_status, clock_cycle):
    #     pass