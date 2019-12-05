import sys
from instruction import Instruction
from processing_unit import ProcessingUnit
from constants import *
import re

# program_file = sys.argv[1]
# data_file = sys.argv[2]
# register_file = sys.argv[3]
# config_file = sys.argv[4]
# # result_file = sys.argv[5]

program_file = "inst.txt"
memory_file = "data.txt"
register_file = "reg.txt"
config_file = "config.txt"
stages_busy_status = {
    IF: False,
    ID: False,
    MEM: False,
    WB: False,
    FINISHED: False
}

instruction_set = []
processing_units = []
clock_cycle = 0

with open(config_file) as config:
    for line in config:
        operands = re.split("[:,]", line)
        pu = ProcessingUnit(operands[0].rstrip().lstrip(), operands[1].rstrip().lstrip() if 1 < len(operands) else None, operands[2].rstrip().lstrip() if 2 < len(operands) else None, None)
        processing_units.append(pu)
processing_units.append(ProcessingUnit(INT_AL, 1, 'yes', None))

register_data_R_series = {}
with open(register_file) as register_data:
    for idx, line in enumerate(register_data):
        register_data_R_series["R"+str(idx)] = int(line, 2)

# register_data_F_series = {}
# for i in range(32):
#     register_data_F_series["F"+str(idx)] = 0

memory_data = {}
with open(memory_file) as file_data:
    for idx, line in enumerate(file_data):
        memory_data[idx+256] = int(line.rstrip(), 2)

with open(program_file) as program:
    for line in program:
        operands = list(filter(lambda character: character != '', re.split("[ ,]", line)))
        inst = Instruction(operands[0].rstrip(), operands[1].rstrip() if 1 < len(operands) else None, operands[2].rstrip() if 2 < len(operands) else None, operands[3].rstrip() if 3 < len(operands) else None, processing_units)
        instruction_set.append(inst)

dependency_dict = {}
program_counter = 0
while(clock_cycle <= 50):
    for instruction in instruction_set:
        safe_to_proceed, instruction_issued = instruction.next_stage_proceed_check(stages_busy_status, dependency_dict)
        if(safe_to_proceed):
            if(instruction_issued): program_counter += 1
            instruction.proceed_to_next_stage(stages_busy_status, clock_cycle, dependency_dict, register_data_R_series, memory_data, instruction_set)
    clock_cycle += 1

for inst in instruction_set:
    print(str(inst).ljust(25) + str(inst.completed_on[IF]).ljust(5) + str(inst.completed_on[ID]).ljust(5) + str(inst.completed_on[EX]).ljust(5) + str(inst.completed_on[MEM]).ljust(5) + str(inst.completed_on[WB]).ljust(5))