import sys
import json
from make_cfg import make_blocks
from collections import namedtuple

LVNTableRow = namedtuple('LVNTableRow', ['index', 'value', 'canonical'])
vars_in_block = namedtuple('vars_in_block', ['reassinged_vars', 'single_assign_vars'])

class LVNTable:

    def __init__(self):
        self.table = [] # list of LVNTableRow
        self.state = {} # var -> row index
        self.valueToRow = {} # value -> row index
    
    # returns true value is in the table
    def __contains__(self, value):
        return value in self.valueToRow
    
    # Returns a LVNTableRow containing value
    def __getitem__(self, val):
        return self.valToRow(val)
    
    # Returns the row that stores the given value
    def valToRow(self, val):
        return self.table[self.valueToRow[val]]

    def appendRow(self, val, canonical):
        row_index = len(self.table)
        row = LVNTableRow(row_index, val, canonical)
        self.table.append(row)
        self.valueToRow[val] = row_index
        return row

    def varInStateToRow(self, var):
        return self.table[self.state[var]]

    def setStateOfVarToIndex(self, var, row_index):
        self.state[var] = row_index

# Return a set 
def find_overwritten_instr_idxs(block_instrs):    
    overwritten_idxs = set()
    seen = set()
    for idx, instr in reversed(list(enumerate(block_instrs))):
        if 'dest' in instr:
            if instr['dest'] in seen:
                overwritten_idxs.add(idx)
            seen.add(instr['dest'])
    return overwritten_idxs
    

def mk_fresh_name(name, used_names):
    if name not in used_names: return name

    i = 0
    new_name = name + '.' + i
    while new_name in used_names:
        i += 1
        new_name = name + '.' + i
    return new_name
        

def lvn_block(block_instrs):
    table = LVNTable()
    new_instrs = []
    overwritten_instr_idxs = find_overwritten_instr_idxs(block_instrs)
    used_names = {instr['dest'] for instr in block_instrs if 'dest' in instr}
    for instr_idx, instr in enumerate(block_instrs):
        if 'op' not in instr:
            # skip labels
            new_instrs.append(instr)
            continue
        new_instr = instr

        # construct value
        value = (instr["op"], instr.get('value', None)) + tuple(table.varInStateToRow(arg) for arg in instr.get("args", []))

        if value in table:
            # The value has been computed before; reuse it.
            row = table[value]
            
            # replace instr with copy of var
            new_instr = {"op": "id", "dest": instr["dest"], "type": instr["type"], "args": [row.canonical]}

            # set state of instr.dest to row
            table.setStateOfVarToIndex(instr["dest"], row.index)
        else:
            if 'dest' in instr:
                # a newly computed value, append to table
                dest = instr['dest']
                
                # if instr will be overwritten block
                if instr_idx in overwritten_instr_idxs:
                    dest = mk_fresh_name(dest, used_names)
                    used_names.add(dest)
                    new_instr['dest'] = dest

                # append row and set as instr.dest state
                new_row = table.appendRow(value, dest)
                table.setStateOfVarToIndex(instr['dest'], new_row.index)

            for arg_idx, a in enumerate(new_instr.get('args', [])):
                # replace a with table[var2num[a]].var
                new_name = table.varInStateToRow(a).canonical
                new_instr['args'][arg_idx] = new_name
        
        new_instrs.append(new_instr)
    return new_instrs

def lvn_func(func_instrs):
    blocks = make_blocks(func_instrs, '', True).values()
    new_instrs = []
    for block in blocks:
        new_instrs.extend(lvn_block(block))
    return new_instrs

def lvn(json_input):
    inp = json.loads(json_input)
    functions = inp['functions']
    for function in functions:
        function['instrs'] = lvn_func(function['instrs'])
    inp['functions'] = functions
    return json.dumps(inp)

if(__name__ == "__main__"):
    print(lvn(sys.stdin.read()))
