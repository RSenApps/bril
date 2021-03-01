import json
import sys
from collections import OrderedDict

TERMINATORS = ['jmp', 'br', 'ret']

def print_blocks(blocks: OrderedDict) -> None:
    for label, block in blocks.items():
        print(label)
        for instr in block:
            print('  ', instr)

def name_block(label, index, fn_name):
    if label:
        return label
    else:
        return fn_name + str(index)

def make_blocks(instrs: list, fn_name: str) -> OrderedDict:
    current_block = []
    blocks = OrderedDict()
    current_label = None
    for instr in instrs:
        if 'label' in instr:
            if current_block:
                blocks[name_block(current_label, len(blocks), fn_name)] = current_block
            current_block = []
            current_label = instr['label']
        elif instr['op'] in TERMINATORS:
            current_block.append(instr)
            blocks[name_block(current_label, len(blocks), fn_name)] = current_block
            current_block = []
            current_label = None
        else:
            current_block.append(instr)
    return blocks

def make_cfg(json_input: str) -> dict:
    functions = json.loads(json_input)['functions']
    instrs = [instr for function in functions for instr in function['instrs']]
    f2blocks = {function['name']: make_blocks(function['instrs'], function['name']) for function in functions}
    cfg = {} # block label key to succs
    for function in functions:
        blocks = f2blocks[function['name']]
        for i, (label, block) in enumerate(blocks.items()):
            succs = []
            for instr in block:
                if instr['op'] == 'jmp':
                    succs.append(instr['labels'][0])
                elif instr['op'] == 'br':
                    succs.extend(instr['labels'])
                elif instr['op'] == 'call':
                    func = instr['funcs'][0]
                    first_block = list(f2blocks[func].items())[0]
                    first_block_label = first_block[0]
                    succs.append(first_block_label)
            if not succs and i + 1 < len(blocks):
                succs.append(list(blocks.keys())[i + 1])
            cfg[label] = succs
    return cfg

if(__name__ == "__main__"):
    cfg = make_cfg(sys.stdin.read())
    print(cfg)