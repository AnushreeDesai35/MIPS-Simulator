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
data_file = "data.txt"
register_file = "reg.txt"
config_file = "config.txt"
# result_file = sys.argv[5]
stages_busy_status = {
    IF: False,
    ID: False,
    EX: False,
    WB: False,
    FINISHED: False
}

instruction_set = []
processing_units = []
clock_cycle = 0

with open(config_file) as config:
    for line in config:
        operands = re.split("[:,]", line)
        pu = ProcessingUnit(operands[0].rstrip(), operands[1].rstrip() if 1 < len(operands) else None, operands[2].rstrip() if 2 < len(operands) else None, None)
        processing_units.append(pu)
processing_units.append(ProcessingUnit(INT_AL, 2, 'yes', None))
processing_units.append(ProcessingUnit(INT_MEMACCESS, 2, 'yes', None))
processing_units.append(ProcessingUnit(FP_MEMACCESS, 2, 'yes', None))

with open(program_file) as program:
    for line in program:
        operands = line.split(" ")
        inst = Instruction(operands[0].rstrip(), operands[1].rstrip() if 1 < len(operands) else None, operands[2].rstrip() if 2 < len(operands) else None, operands[3].rstrip() if 3 < len(operands) else None, processing_units)
        instruction_set.append(inst)

program_counter = 0
while(clock_cycle <= 50):
    for instruction in instruction_set:
        safe_to_proceed, instruction_issued = instruction.next_stage_proceed_check(stages_busy_status, clock_cycle)
        if(safe_to_proceed):
            if(instruction_issued): program_counter += 1
            instruction.proceed_to_next_stage(stages_busy_status, clock_cycle)
    clock_cycle += 1

for inst in instruction_set:
    print(str(inst).ljust(25) + str(inst.completed_on[IF]).ljust(5) + str(inst.completed_on[ID]).ljust(5) + "  " + str(inst.completed_on[EX]).ljust(5) + "  " + str(inst.completed_on[WB]).ljust(5))