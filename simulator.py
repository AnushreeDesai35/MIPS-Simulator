import sys
from instruction import Instruction
from processing_unit import ProcessingUnit
from constants import *
import re

program_file = sys.argv[1]
memory_file = sys.argv[2]
register_file = sys.argv[3]
config_file = sys.argv[4]
result_file = sys.argv[5]

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

label_data = {}
with open(program_file) as program:
    for idx, line in enumerate(program):
        label = None
        operands = []
        reg = None
        base = None
        label_check = re.split(":", line)
        if len(label_check) == 2:
            operands = list(filter(lambda character: character != '', re.split("[ ,]", label_check[1])))
            label = label_check[0]
            label_data[label] = idx
        else:
            operands = list(filter(lambda character: character != '', re.split("[ ,]", line)))
        if(len(operands) > 2):
            op = operands[2].rstrip()
            tempstr = re.split("[()]", op)
            if(len(tempstr)>1):
                base = tempstr[0]
                reg = tempstr[1]
            else:
                reg = tempstr[0]
        inst = Instruction(operands[0].rstrip(), operands[1].rstrip() if 1 < len(operands) else None, reg, operands[3].rstrip() if 3 < len(operands) else None, label, processing_units, base)
        instruction_set.append(inst)

dependency_dict = {}
program_counter = -1
i_cache = [[],[],[],[]]
inst_length = len(instruction_set)
while(clock_cycle <= 200):
    for idx, instruction in enumerate(instruction_set):
        safe_to_proceed, instruction_issued = instruction.next_stage_proceed_check(stages_busy_status, dependency_dict)
        if(safe_to_proceed):
            instruction.proceed_to_next_stage(stages_busy_status, clock_cycle, dependency_dict, register_data_R_series, memory_data, instruction_set, label_data, idx, processing_units, i_cache, program_counter, inst_length)
            if(instruction_issued): program_counter += 1
    clock_cycle += 1


with open(result_file, 'w') as f:
    f.write(str("Instruction").ljust(25) + str("FT").ljust(5) + str("ID").ljust(5) + str("EX").ljust(5) + str("WB").ljust(5) + str("RAW").ljust(5) + "WAR".ljust(5) + "WAW".ljust(5) + "Struct".ljust(5))
    for inst in instruction_set:
        ex_cycles = str(inst.completed_on[MEM]).ljust(5) if(inst.name in UNIT_INST_MAP[INT_AL] + DATA_TRANSFER) else str(inst.completed_on[EX]).ljust(5)
        inst_name = inst.label + ":" +str(inst) if (inst.label) else str(inst)
        f.write("\n")
        f.write(inst_name.ljust(25) + str(inst.completed_on[IF]).ljust(5) + str(inst.completed_on[ID]).ljust(5) + ex_cycles + str(inst.completed_on[WB]).ljust(5) + inst.raw.ljust(5) + inst.war.ljust(5) + inst.waw.ljust(5) + inst.struct.ljust(5))