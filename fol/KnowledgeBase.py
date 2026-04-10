from fol.Clause import *
from fol.Literal import Literal

class KnowledgeBase:
    facts: set[Literal] = set()
    generative_clauses: list[GenerativeClause] = []
    definite_clauses: list[DefiniteClause] = []

    def __init__(self):
        pass

    def __init__(self):
        self.facts = set()
        self.generative_clauses = []
        self.definite_clauses = []
    
    def add_genertive_clause(self, clause: GenerativeClause):
        self.generative_clauses.append(clause)

    def add_defnite_clause(self,clause: DefiniteClause):
        self.definite_clauses.append(clause)

    def add_fact(self, fact: Literal):
        self.facts.add(fact)

    def is_known(self, theory: Literal):
        return theory in self.facts

