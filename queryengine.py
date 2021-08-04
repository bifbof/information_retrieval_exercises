#!/usr/bin/env python3

from queryparser import parse_query, ast_has_operation, process_ast, Operation, ParseException
from textutils import tokenize_document

# XXX: copied from notebook
from collections import namedtuple
PostingsList = namedtuple('PostingsList', ['termid', 'postings'])
def read_postings_list(fh):
    '''
    Read postings list from file at fh
    Expected format:  'termid:docid,docid,...,docid'
    '''
    line = fh.readline().strip()
    try:
        termid, postingstr = line.split(':')
        postings = list(map(int, postingstr.split(',')))
        return PostingsList(termid=int(termid), postings=postings)
    except:
        if line != '':
            # This is an actual parse error, empty line just signals EOF.
            print("Unable to parse line '%s' as postings list" % line)
        return None


class InvertedIndex(object):
    '''
    A class which implements a simple inverted index built from standard
    python datastructures.  We use python's dict to represent dictionarys, and
    python lists to represent posting lists.  For now we keep everything in
    memory.
    '''

    '''Map document ids to document files'''
    _documents = {}
    '''Map terms to term ids -> for query parsing'''
    _terms = {}
    '''Map termids to terms -> for query parsing'''
    _termids = {}
    '''The posting lists'''
    _the_index = {}

    def __init__(self, indexfile='index.bin', termmap='termid_map.bin',
                 docmap='docid_map.bin'):
        '''
        Construct in-memory inverted index from output of blocked sort-based
        index construction code.
        '''
        with open(docmap, 'r') as f:
            for line in f:
                docid, docpath = line.strip().split(':')
                docid = int(docid)
                self._documents[docid] = docpath
        with open(termmap, 'r') as f:
            for line in f:
                term, termid = line.strip().split(':')
                termid = int(termid)
                self._terms[term] = termid
                self._termids[termid] = term

        with open(indexfile, 'r') as f:
            while True:
                pl = read_postings_list(f)
                if not pl:
                    break
                self._the_index[pl.termid] = pl.postings

    def _intersect_two(self, p1, p2):
        '''
        Intersect two posting lists according to pseudo-code in Introduction
        to Information Retrieval, Figure 1.6
        '''
        answer = []
        while p1 != [] and p2 != []:
            if p1[0] == p2[0]:
                answer.append(p1[0])
                p1 = p1[1:]
                p2 = p2[1:]
            elif p1[0] < p2[0]:
                p1 = p1[1:]
            else:
                p2 = p2[1:]
        return answer

    def _intersect(self, terms):
        '''
        Intersect posting lists for a list of termids, according to pseudo-code
        in Introduction to Information Retrieval, Figure 1.7
        '''
        postings = [ self._the_index[t] if t > 0 else self._negate(-t) for t in terms ]
        # calculate word frequencies and sort term,freq pairs in ascending
        # order by frequency
        freqs = sorted([ (t, len(p)) for t,p in zip(terms, postings) ], key=lambda x: x[1] )
        terms, _ = map(list,zip(*freqs))
        if terms[0] < 0:
            result = self._negate(-terms[0])
        else:
            result = self._the_index[terms[0]]
        terms = terms[1:]
        while terms != [] and result != []:
            if terms[0] < 0:
                ps = self._negate(-terms[0])
            elif terms[0] == 0:
                ps = []
            else:
                ps = self._the_index[terms[0]]
            result = self._intersect_two(result, ps)
            terms = terms[1:]
        return result

    def _negate(self, term):
        if term in self._the_index.keys():
            return sorted(set(self._documents.keys()) - set(self._the_index[term]))
        else:
            # What is the correct negation of a term not 
            return list(self._documents.keys())

    def _execute_query_tree(self, flat):
        result = set()
        if flat.op == 'AND':
            result = set(self._documents.keys())
        for arg in flat.args:
            # execute subtree etc
            if isinstance(arg, Operation):
                temp = self._execute_query_tree(arg)
            else:
                assert(isinstance(arg, str))
                termid = 0
                if arg.startswith('-') and arg[1:] in self._terms:
                    termid = -self._terms[arg[1:]]
                    temp = self._negate(termid)
                elif arg.startswith('-'):
                    # Negated term that does not exist in dictionary:
                    # NOT -> set(documents)
                    # OR -> set(documents)
                    # AND -> empty set
                    if flat.op == 'AND':
                        temp = set()
                    else:
                        temp = set(self._documents.keys())
                elif arg in self._terms:
                    termid = self._terms[arg]
                    temp = self._the_index[termid]

                if flat.op == 'OR':
                    result = result | set(temp)
                elif flat.op == 'AND':
                    result = result & set(temp)
                elif flat.op == 'NOT':
                    assert(len(flat.args) == 1)
                    result = set(self._documents.keys()) - set(temp)

        return sorted(result)

    def execute_query(self, query):
        '''
        Execute a boolean query on the inverted index. We only support single
        operator queries ATM.  This method returns a list of document ids
        which satisfy the query in no particular order (i.e. the order in
        which the documents were added most likely :)).
        '''
        # We use a generated parser to transform the query from a string to an
        # AST.
        try:
            ast = parse_query(query)
        except ParseException as e:
            print("Failed to parse query '%s'\n" % query, e)
            return None

        # We preprocess the AST to flatten commutative operations, such as
        # sequences of ANDs. We also transform 'NOT <term>' arguments into
        # '-<term>' to allow smarter processing of AND NOT and OR NOT.
        flat = process_ast(ast)

        args = []
        # go through arguments and fall back on recursive evaluation if we
        # could not completely flatten the query
        for arg in flat.args:
            if isinstance(arg, Operation):
                # as soon as we find a argument to the top-level operation
                # which is not just a term, we fall back on the tree query
                # execution strategy.
                return self._execute_query_tree(flat)
            else:
                # Convert terms to term ids for querying
                # XXX magic value
                termid = 0
                if arg.startswith('-') and arg[1:] in self._terms:
                    termid = -self._terms[arg[1:]]
                elif arg.startswith('-'):
                    # We don't care about top-level OR NOT, and for AND we can
                    # drop top-level NOT clause for term that does not exist
                    # in dictionary
                    continue
                elif arg in self._terms:
                    termid = self._terms[arg]
                args.append(termid)

        if flat.op == 'OR':
            results = set()
            for arg in args:
                if arg < 0:
                    results = results | set(self._negate(-arg))
                else:
                    results = results | set(self._the_index[arg])
            return sorted(results)

        elif flat.op == 'AND':
            return self._intersect(args)

        elif flat.op == 'NOT':
            # handle case where we query for the negation of a term not in the
            # vocabulary.
            if len(args) == 0:
                return list(self._documents.keys())
            else:
                assert(len(args) == 1)
                return sorted(set(self._documents.keys()) - set(self._the_index[args[0]]))

        elif flat.op == 'LOOKUP':
            if len(args) == 0:
                # we drop terms that are not in the vocabulary in the
                # preprocessing loop, so handle the case where we query for a
                # single term that is not in the vocabulary.
                return []
            else:
                # in this case the query was a single term
                assert(len(args) == 1)
                return self._the_index[args[0]]
        else:
            print("Cannot handle query '%s', aborting..." % query)
            return None

    def documents_for_ids(self, docids):
        '''
        Return a list of document names for the passed document IDs
        '''
        return [ self._documents[docid] for docid in docids ]

    def dump(self):
        print("Inverted index:")
        print("Documents:")
        for docid in sorted(self._documents):
            print("%d -> %s" % (docid, self._documents[docid]))
        print("Posting lists:")
        for termid in sorted(self._the_index.keys()):
            print("%d(%s) -> %r" % (termid, self._termids[termid], self._the_index[termid]))

    def execute_and_print(self, query):
        '''
        Execute query and print human-readable results
        '''
        docids = self.execute_query(query)
        if not docids:
            print("No documents found")
            print()
            return
        # If we got some results, print them
        docs = self.documents_for_ids(docids)
        for docid,doc in zip(docids,docs):
            print('%d -> %s' % (docid, doc))
        print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: %s <indexfile> <termmap> <docmap>" % sys.argv[0])
        sys.exit(1)
    ii = InvertedIndex(indexfile=sys.argv[1], termmap=sys.argv[2],
                       docmap=sys.argv[3])

    for query in sys.argv[4:]:
        docids = ii.execute_query(query)
        if docids is None:
            print("Error while executing query.")
        elif docids:
            print("Documents matching '%s':" % query)
            docs = ii.documents_for_ids(docids)
            results = [ '%2d -> %s' % (docid, doc) for docid, doc in zip(docids, docs) ]
            print('\n'.join(results))
        else:
            print("No documents match '%s'" % query)