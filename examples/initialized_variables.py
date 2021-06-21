import sys
import json
from make_cfg import make_cfg, make_blocks
from collections import namedtuple, defaultdict

class DataFlow:
    def init(self, funcArgs):
        raise NotImplementedError
    
    def transfer(self, block, inBlock):
        raise NotImplementedError
    
    def merge(self, inList):
        raise NotImplementedError

def constructPreds(cfg):
    reversed_cfg = defaultdict(list)
    for label, succs in cfg.items():
        for succ in succs:
            reversed_cfg[succ].append(label)
    return reversed_cfg

def dataFlowSolver(args, cfg, blocksDict, dataFlowProblem):
    listOfBlocks = list(blocksDict.items())
    inBlocks = {}
    inBlocks[listOfBlocks[0][0]] = dataFlowProblem.init(args) # inBlocks[label of first block]
    outBlocks = {block[0]: dataFlowProblem.init(args) for block in listOfBlocks}
    reversed_cfg = constructPreds(cfg)

    worklist = listOfBlocks
    while worklist:
        currentBlock = worklist.pop()
        if reversed_cfg[currentBlock[0]]:
            inBlocks[currentBlock[0]] = dataFlowProblem.merge([ outBlocks[label].copy() for label in reversed_cfg[currentBlock[0]] ])

        oldOut = outBlocks[currentBlock[0]]
        outBlocks[currentBlock[0]] = dataFlowProblem.transfer(currentBlock[1], inBlocks[currentBlock[0]].copy())
        # DEBUG print(currentBlock[0], inBlocks[currentBlock[0]], outBlocks[currentBlock[0]])

        if outBlocks[currentBlock[0]] != oldOut:
            worklist.extend( [(label, blocksDict[label]) for label in cfg[currentBlock[0]]] )
    return outBlocks

# Variable is considered initialized in a block if variable is initialized in all predecessors
# or if the variable is initialized in the block
# Note: this definition could be stronger as not all predecessors are visited before this block
# for example a predecessor that is dominated by this block could be safely ignored when taking the interesection
# but this does not follow the dataflow pattern
class InitializedDataFlow(DataFlow):
    def init(self, funcArgs):
        return {arg['name'] for arg in funcArgs}

    def transfer(self, block, inBlock):
        inBlock.update(self.initialized_vars(block))
        return inBlock
    
    def merge(self, inList):
        if len(inList) == 0:
            return set()
        s = inList[0]
        for otherS in inList[1:]:
            s = s.intersection(otherS)
        return s

    def initialized_vars(self, block):
        initialized = set()
        for instr in block:
            if 'dest' in instr:
                initialized.add(instr['dest'])
        return initialized

def initialized(json_input):
    inp = json.loads(json_input)
    functions = inp['functions']
    cfg = make_cfg(json_input)
    for function in functions:
        blocks = make_blocks(function['instrs'], function['name'])
        print(dataFlowSolver(function.get('args', []), cfg, blocks, InitializedDataFlow()))
        
if(__name__ == "__main__"):
    initialized(sys.stdin.read())
