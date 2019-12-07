from constants import *
import re
from d_cache import *
dcache_obj = D_cache()
class Instruction:
    def __init__(self, name, destination_register=None, source_register1=None, source_register2=None, label=None, processing_units = [], base=None):
        self.name = name.split(',')[0].upper()
        self.destination_register = destination_register.split(',')[0] if(destination_register != None) else None
        self.source_register1 = source_register1
        self.source_register2 = source_register2.split(',')[0].upper() if(source_register2 != None) else None
        self.base = base
        self.current_stage = 0
        self.remaning_cycles = 1
        self.finished = False
        self.i_cache_set = False
        self.unit = self.find_inst_unit(processing_units)
        self.execution_cycles = self.calculate_execution_cycles(processing_units)
        self.memory_cycles = self.calculate_memory_cycles(processing_units)
        self.destination_register_value = None
        self.label = label
        self.raw = "N"
        self.war = "N"
        self.waw = "N"
        self.struct = "N"
        self.completed_on = {
            IF: None,
            ID: None,
            EX: None,
            MEM: None,
            WB: None
        }
        self.i_type = ""
        if self.name in DATA_TRANSFER:
            self.i_type = DATA_TRANSFER
        elif self.name in ARITHMETIC_LOGICAL:
            self.i_type = ARITHMETIC_LOGICAL
        elif self.name in CONTROL:
            self.i_type = CONTROL
        else:
            self.i_type = SPECIAL

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
        waw = self.check_WAW(dependency_dict)
        if raw:
            self.raw = "Y"
            return False, issued
        if waw:
            self.waw = "Y"
            return False, issued

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

            if(self.name in CONTROL):
                sr1_check = source_register1 in dependency_dict and dependency_dict[source_register1] != None
                sr2_check = self.destination_register in dependency_dict and dependency_dict[self.destination_register] != None
            return sr1_check or sr2_check
        else: return False
    
    def check_WAW(self, dependency_dict):
        if(self.current_stage == ID):
            if(self.name not in CONTROL):
                return self.destination_register in dependency_dict and dependency_dict[self.destination_register] != None
            else: return False
        else: return False

    def proceed_to_next_stage(self, stages_busy_status, clock_cycle, dependency_dict, register_data_R_series, memory_data, instruction_set, label_data, idx, processing_units, i_cache, program_counter, inst_length):
        if(self.current_stage == 0): self.issue_instruction(stages_busy_status)
        elif(self.current_stage == IF): self.goto_ID_stage(stages_busy_status, clock_cycle, dependency_dict, i_cache, program_counter, processing_units, instruction_set, inst_length)
        elif(self.current_stage == ID): self.goto_EX_stage(stages_busy_status, clock_cycle, dependency_dict, register_data_R_series, memory_data, instruction_set, label_data, idx, processing_units)
        elif(self.current_stage == EX): self.goto_MEM_or_WB_stage(stages_busy_status, clock_cycle, dependency_dict)
        elif(self.current_stage == MEM): self.goto_WB_stage(stages_busy_status, clock_cycle, dependency_dict)
        elif(self.current_stage == WB): self.goto_FINISH_stage(stages_busy_status, clock_cycle, dependency_dict, register_data_R_series)

    def issue_instruction(self, stages_busy_status):
        self.current_stage += 1
        stages_busy_status[IF] = True

    def goto_ID_stage(self, stages_busy_status, clock_cycle, dependency_dict, i_cache, program_counter, processing_units, instruction_set, inst_length):

        if self.i_cache_set:
            self.remaning_cycles -= 1
            if self.remaning_cycles == 0:
                self.i_cache_set = False
                self.current_stage += 1
                stages_busy_status[IF] = False
                stages_busy_status[ID] = True
                self.completed_on[IF] = clock_cycle
        else:
            self.i_cache_set = True
            program_counter = program_counter % 16
            block = int(program_counter / 4)
            base = block * 4
            if program_counter not in i_cache[block]:
                self.remaning_cycles = (2 * int(list(filter(lambda pu: pu.name == MAIN_MEMORY, processing_units))[0].cycle_count) + int(list(filter(lambda pu: pu.name == INSTRUCTION_CACHE, processing_units))[0].cycle_count))
                i_cache[block] = tuple(map(lambda x: x + base, range(0,4)))
            else:
                self.remaning_cycles = int(list(filter(lambda pu: pu.name == INSTRUCTION_CACHE, processing_units))[0].cycle_count)
                self.i_cache_set = False
                self.current_stage += 1
                stages_busy_status[IF] = False
                stages_busy_status[ID] = True
                self.completed_on[IF] = clock_cycle

    def goto_EX_stage(self, stages_busy_status, clock_cycle, dependency_dict, register_data_R_series, memory_data, instruction_set, label_data, idx, processing_units):
        if (self.name in UNIT_INST_MAP[INT_AL] + [LOAD, STORE]): self.perform_execution(register_data_R_series, memory_data)
        # if (self.name in [LOAD, LOAD_DOUBLE, STORE, STORE_DOUBLE]):
        #     dcache_obj.cache_check(register_data_R_series[self.source_register1]+self.base)

        if(self.name in CONTROL):

            bne = self.name == BRANCH_NOT_EQUAL
            beq = self.name == BRANCH_EQUAL
            J = self.name == UNCONDITIONAL_JUMP
            trailing_inst = instruction_set[idx+2:]
            if (bne and register_data_R_series[self.source_register1] != register_data_R_series[self.destination_register]) or (beq and register_data_R_series[self.source_register1] == register_data_R_series[self.destination_register]) or J:

                start = label_data[self.source_register2]
                label_data[self.source_register2] = len(instruction_set[label_data[self.source_register2]:idx+1]) - 1 + len(trailing_inst)

                for extra in instruction_set[idx+2:]:
                    instruction_set.remove(extra)

                for i in instruction_set[start:idx+2]:
                    newint = Instruction(i.name, i.destination_register, i.source_register1, i.source_register2, i.label, processing_units, self.base)
                    instruction_set.append(newint)
            else:       
                instruction_set.extend(trailing_inst)

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

    def goto_MEM_or_WB_stage(self, stages_busy_status, clock_cycle, dependency_dict):
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
        else:
            self.struct = "Y"
            
    def goto_WB_stage(self, stages_busy_status, clock_cycle, dependency_dict):
        self.memory_cycles -= 1
        if(self.memory_cycles == 0):
            self.current_stage += 1
            stages_busy_status[MEM] = False
            self.completed_on[MEM] = clock_cycle
            stages_busy_status[WB] = True
        else:
            self.struct = "Y"

    def goto_FINISH_stage(self, stages_busy_status, clock_cycle, dependency_dict, register_data_R_series):
            register_data_R_series[self.destination_register] = self.destination_register_value
            self.completed_on[WB] = clock_cycle
            self.finished = True
            stages_busy_status[WB] = False
            dependency_dict[self.destination_register] = None

    def perform_execution(self, register_data_R_series, memory_data):
        if(self.name == LOAD):
            self.destination_register_value = memory_data[int(self.base) + register_data_R_series(self.source_register1)]
        elif(self.name == STORE):
            memory_data[int(self.base) + register_data_R_series[self.source_register1]] = self.destination_register
        elif(self.name == ADD_SIGNED):
            self.destination_register_value = register_data_R_series[self.source_register1] + register_data_R_series[self.source_register2]
        elif(self.name == ADD_IMMEDIATE_SIGNED):
            self.destination_register_value = register_data_R_series[self.source_register1] + int(self.source_register2)
        elif(self.name == SUBTRACT_SIGNED):
            self.destination_register_value = register_data_R_series[self.source_register1] - register_data_R_series[self.source_register2]
        elif(self.name == SUBTRACT_IMMEDIATE_SIGNED):
            self.destination_register_value = register_data_R_series[self.source_register1] - int(self.source_register2)
        elif(self.name == AND_BITWISE):
            self.destination_register_value = register_data_R_series[self.source_register1] & register_data_R_series[self.source_register2]
        elif(self.name == AND_BITWISE_IMMEDIATE):
            self.destination_register_value = register_data_R_series[self.source_register1] & int(self.source_register2)
        elif(self.name == OR_BITWISE):
            self.destination_register_value = register_data_R_series[self.source_register1] | register_data_R_series[self.source_register2]
        elif(self.name == OR_BITWISE_IMMEDIATE):
            self.destination_register_value = register_data_R_series[self.source_register1] | int(self.source_register2)