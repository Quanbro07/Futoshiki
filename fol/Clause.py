from abc import ABC
from fol.Literal import Literal
from fol.Predicate import *

class Clause(ABC):
    pass

# A v B v ¬C
class GenerativeClause(Clause):
    literals: list[Literal]

    def __init__(self, literals: list[Literal]):
        self.literals = literals

    def is_unit(self) -> bool:
        return len(self.literals) == 1
    
    def is_empty(self) -> bool:
        return len(self.literals) == 0
    
    def __repr__(self):
        return " V ".join(str(lit) for lit in self.literals)


# A ∧ B => C
class DefiniteClause(Clause):
    
    conditions: list[Literal]
    conclusion: Literal

    def __init__(self, conditions: list[Literal], conclusion: Literal):
        self.conditions = conditions
        self.conclusion = conclusion
    

    def is_conditions_satified(self,facts: set[Literal]):
        
        for condition in self.conditions:
            if condition not in facts:
                return False

        return True

    def __repr__(self):
        body = " ∧ ".join(str(c) for c in self.conditions)
        return f"{body} → {self.conclusion}"
    

def main():
    genClause = GenerativeClause([
        Literal(Val(1,1,1), True),
        Literal(Val(1,1,2), False),
        Literal(Val(1,1,3), False),
        Literal(Val(1,1,4), False),
    ])

    deClause = DefiniteClause(
        conclusion = Literal(Val(1,1,2), False),
        conditions = [Literal(Given(1,1,2), False)]
    )

    print(genClause)
    print(deClause)


if __name__ == "__main__":
    main()