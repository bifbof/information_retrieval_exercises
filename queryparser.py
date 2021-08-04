from astparser import BooleanQueryParser
from tatsu.ast import AST
from tatsu.exceptions import ParseException

_parser = BooleanQueryParser()

def ast_has_operation(ast):
    '''
    Check whether the passed AST contains an operation.

    This function will return false for a query that consists of a single term
    '''
    return isinstance(ast, AST) and ast.op is not None

def parse_query(query):
    '''
    Parse boolean query and return resulting AST
    '''
    return _parser.parse(query)

class Operation(object):
    '''
    A representation of a boolean query operation.  The `op` field represents
    the operation type which should be one of `AND`, `OR`, `NOT`, or
    `LOOKUP`.
    The `args` field is a list of one or more arguments for the operation.
    `NOT` and `LOOKUP` operations are expected to have a argument list of
    length one. `AND`, and `OR` can have arbitrarily long argument lists, but
    the argument list for such an operation should contain at least two
    elements.
    For `AND` and `OR`, we represent operands of the form 'NOT <term>' as
    the string '-<term>' to allow more efficient execution of queries of the
    form 'a AND NOT b' and 'a OR NOT b'.
    '''
    def __init__(self, op, args):
        self.op = op
        self.args = args

    def __repr__(self):
        return "%s: args=%r" % (self.op, self.args)

    def add_arg(self, arg):
        if arg.op == self.op:
            self.args.extend(arg.args)
        elif arg.op == 'NOT' and isinstance(arg.args[0], str):
            self.args.append('-%s' % arg.args[0])
        elif arg.op == 'LOOKUP':
            self.args.append(arg.args[0])
        else:
            self.args.append(arg)

def process_ast(ast):
    '''
    Preprocess a single ast node and return elements in more uniform manner
    This function flattens tree structures made up of only ANDs or ORs
    '''
    if not isinstance(ast, AST):
        return Operation('LOOKUP', [ast])

    assert(isinstance(ast, AST))
    if ast.op is not None:
        op = ast.op
        if isinstance(ast.op, list):
            assert(len(set(ast.op)) == 1)
            op = ast.op[0]
        if op == 'NOT':
            assert(ast.lst is None)
            if not isinstance(ast.fst, AST):
                return Operation(op, [ ast.fst ])

        assert(ast.fst is not None)
        o = Operation(op, [])
        fst = process_ast(ast.fst)
        o.add_arg(fst)

        if ast['lst'] is not None:
            if isinstance(ast.lst, list):
                for a in ast.lst:
                    a = process_ast(a)
                    o.add_arg(a)
            else:
                lst = process_ast(ast.lst)
                o.add_arg(lst)

        return o

    else:
        assert(ast.lst is None)
        if isinstance(ast.fst, AST):
            return process_ast(ast.fst)
        else:
            return Operation('LOOKUP', [ast.fst])

def operation_is_complex(oper):
    '''
    Check whether the passed Operation object constitutes a complex query,
    i.e. a query which contains subqueries.
    '''
    for arg in oper.args:
        if isinstance(arg, Operation):
            return True
    return False

if __name__ == "__main__":
    print("Testing query parser wrapper")
    print()
    queries = [
        'Caesar',
        'NOT Caesar',
        'Caesar AND Cleopatra',
        'Caesar AND Brutus AND Cleopatra',
        'Caesar AND (Brutus OR Hamlet) AND Cleopatra',
        'Caesar AND (Brutus OR Hamlet)',
        '( b OR h )',
        'a AND NOT b',
        'Caesar OR Cleopatra AND Brutus',
        'Caesar AND Cleopatra OR Brutus',
        'NOT Caesar AND Cleopatra OR Brutus',
    ]
    for q in queries:
        print(q)
        print()
        ast = parse_query(q)
        print(ast)
        print()
        flat = process_ast(ast)
