import sys
import json
from make_cfg import make_blocks

# Remove unused instructions
def function_level_dce_pass(func_instrs):
    old_size = None
    cur_size = len(func_instrs)

    while old_size is None or old_size != cur_size:
        var_to_instr_idx = dict()

        # Scan 1: Add all defs
        for idx, instr in enumerate(func_instrs):
            if 'dest' in instr:
                var_to_instr_idx[instr['dest']] = idx
            
        # Scan 2: remove all uses (should be left with defs w/o any uses)
        for idx, instr in enumerate(func_instrs):
            for var in instr.get('args', []):
                var_to_instr_idx.pop(var, None)

        instr_indices = set(var_to_instr_idx.values())
        func_instrs = [func_instrs[i] for i in range(len(func_instrs)) if i not in instr_indices]
        old_size = cur_size
        cur_size = len(func_instrs)
    
    return func_instrs

# return block without reassignments
def block_level_reassign_dce_pass(block_instrs):
    last_def_not_used_to_instr_idx = {}
    removed_idxs = set()
    for idx, instr in enumerate(block_instrs):
        # Check for variables that have been used
        if 'args' in instr:
            for var in instr['args']:
                last_def_not_used_to_instr_idx.pop(var, None)


        if 'dest' in instr:
            # Check for any defined variables still in last def not used dict
            # Any defined variables in the set are not used and can be removed.
            if instr['dest'] in last_def_not_used_to_instr_idx:
                removed_idxs.add(last_def_not_used_to_instr_idx[instr['dest']])

            # Update the last def dict with the most recent variable definition
            last_def_not_used_to_instr_idx[instr['dest']] = idx
    
    return [instr for idx, instr in enumerate(block_instrs) if idx not in removed_idxs]

def reassign_dce_pass(func_instrs):
    blocks = make_blocks(func_instrs, '', True).values()
    new_instrs = []
    for block in blocks:
        last_len = None
        cur_instrs = block
        while last_len is None or last_len != len(cur_instrs):
            last_len = len(cur_instrs)
            cur_instrs = block_level_reassign_dce_pass(cur_instrs)
        new_instrs.extend(cur_instrs)
    return new_instrs

def dce(json_input):
    inp = json.loads(json_input)
    functions = inp['functions']
    for function in functions:
        function['instrs'] = function_level_dce_pass(function['instrs'])
        function['instrs'] = reassign_dce_pass(function['instrs'])
    inp['functions'] = functions
    return json.dumps(inp)

if(__name__ == "__main__"):
    print(dce(sys.stdin.read()))
