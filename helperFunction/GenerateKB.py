from helperFunction.ParseInput import parse_input
from fol.KnowledgeBase import KnowledgeBase
from fol.Literal import Literal
from fol.Predicate import *
from fol.Clause import GenerativeClause, DefiniteClause

def generate_KB(inputFile) -> KnowledgeBase:
    N, given, less_h, greater_h, less_v, greater_v = parse_input(inputFile)

    kb = KnowledgeBase()
    rows = cols = vals = range(1, N + 1)

    #──────── A1: Mỗi ô có ít nhất 1 giá trị ────────────
    # ∀i ∀j ∃v Val(i,j,v)
    # Val(i,j,1) OR Val(i,j,2) OR ... OR Val(i,j,N)
    for i in rows:
        for j in cols:
            lits = [Literal(Val(i,j, v)) for v in vals]
            kb.add_genertive_clause(GenerativeClause(lits))

    #──────── A2: Mỗi ô có nhiều nhất 1 giá trị ────────────
    # ∀i ∀j ∀v1 ∀v2 Val(i,j,v1) ∧ Val(i,j,v2) ⇒ v1 = v2
    # NOT Val(i,j,v1) OR NOT Val(i,j,v2)
    for i in rows:
        for j in cols:
            for v1 in vals:
                for v2 in range(v1 + 1, N + 1):
                    kb.add_genertive_clause(GenerativeClause([
                        Literal(Val(i,j,v1), isNegative=True),
                        Literal(Val(i,j,v2), isNegative=True)
                    ]))

    #──────── A3: Row Unique ────────────        
    # ∀i∀j1 ∀j2 ∀v [Val(i,j1,v) ∧ Val(i,j2,v) ∧ j1 ̸= j2] ⇒ ⊥
    # NOT Val(i,j1,v) OR NOT Val(i,j2,v)
    for i in rows:
        for j1 in cols:
            for j2 in range(j1 + 1, N + 1):
                for v in vals:
                    kb.add_genertive_clause(GenerativeClause([
                            Literal(Val(i,j1,v), isNegative=True),
                            Literal(Val(i,j2,v), isNegative=True)
                    ]))

    #──────── A4: Col Unique ────────────        
    # ∀i∀j1 ∀j2 ∀v [Val(i1,j,v) ∧ Val(i2,j,v) ∧ i1 ̸= i2] ⇒ ⊥
    # NOT Val(i1,j,v) OR NOT Val(i2,j,v)
    for i1 in rows:
        for i2 in range(i1 + 1, N + 1):
            for j in cols:
                for v in vals:
                    kb.add_genertive_clause(GenerativeClause([
                            Literal(Val(i1,j,v), isNegative=True),
                            Literal(Val(i2,j,v), isNegative=True)
                    ]))

    #──────── A5: Horizontal Less H ────────────  
    #∀i∀j ∀v1 ∀v2 LessH(i,j) ∧Val(i,j,v1) ∧ Val(i,j+1,v2) ⇒ Less(v1,v2)
    # LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2) ⇒ Less(v1,v2)
    for i in rows:
        for j in range(1,N):
            if (i,j) in less_h:
                kb.add_fact(Literal(LessH(i,j)))
                for v1 in vals:
                    for v2 in range(v1 + 1, N + 1):
                        kb.add_defnite_clause(DefiniteClause(
                            conditions= [
                                Literal(LessH(i, j)),
                                Literal(Val(i, j, v1)),
                                Literal(Val(i, j+ 1,v2))
                            ],
                            conclusion= Literal(Less(v1,v2))
                        ))
    
    #──────── A6: Horizontal Greater H ────────────  
    #∀i∀j ∀v1 ∀v2 GreaterH(i,j) ∧Val(i,j,v1) ∧ Val(i,j+1,v2) ⇒ Greater(v1,v2)
    # GreaterH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2) ⇒ Less(v2,v1)
    for i in rows:
        for j in range(1,N):
            if (i,j) in greater_h:
                kb.add_fact(Literal(GreaterH(i,j)))
                for v1 in vals:
                    for v2 in range(v1 + 1, N + 1):
                        kb.add_defnite_clause(DefiniteClause(
                            conditions= [
                                Literal(GreaterH(i, j)),
                                Literal(Val(i, j, v1)),
                                Literal(Val(i, j+ 1,v2))
                            ],
                            conclusion= Literal(Less(v2,v1))
                        ))

    #──────── A7: Vertical Less V ────────────  
    #∀i∀j ∀v1 ∀v2 GreaterH(i,j) ∧Val(i,j,v1) ∧ Val(i + 1,j,v2) ⇒ Less(v1,v2)
    # LessV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2) → Less(v1,v2)
    for i in range(1,N):
        for j in cols:
            if (i,j) in less_v:
                kb.add_fact(Literal(LessV(i,j)))
                for v1 in vals:
                    for v2 in range(v1 + 1, N + 1):
                        kb.add_defnite_clause(DefiniteClause(
                            conditions= [
                                Literal(LessV(i, j)),
                                Literal(Val(i, j, v1)),
                                Literal(Val(i + 1, j,v2))
                            ],
                            conclusion= Literal(Less(v1,v2))
                        ))

    #──────── A8: Vertical Greater V ────────────  
    #∀i∀j ∀v1 ∀v2 GreaterH(i,j) ∧Val(i,j,v1) ∧ Val(i + 1,j,v2) ⇒ Greater(v1,v2)
    # GreaterV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2) → Less(v2,v1)
    for i in range(1,N):
        for j in cols:
            if (i,j) in greater_v:
                kb.add_fact(Literal(GreaterV(i,j)))
                for v1 in vals:
                    for v2 in range(v1 + 1, N + 1):
                        kb.add_defnite_clause(DefiniteClause(
                            conditions= [
                                Literal(GreaterV(i, j)),
                                Literal(Val(i, j, v1)),
                                Literal(Val(i + 1, j,v2))
                            ],
                            conclusion= Literal(Less(v2,v1))
                        ))

    #──────── A9: Given Clue ──────────── 
    # ∀i ∀j ∀v Given(i,j,v) ⇒ Val(i,j,v)
    # Given(i,j,v) → Val(i,j,v)
    for (i,j), v in given.items():
        kb.add_fact(Literal(Given(i,j,v)))

        kb.add_defnite_clause(DefiniteClause(
            conditions=[Literal(Given(i,j,v))],
            conclusion=Literal(Val(i,j,v))
        ))
    
    return kb

def main():
    input = r"D:\US\Nam_2_HK_2\Co So Tri Tue Nhan Tao\Project\Project_2\test.txt"
    kb = generate_KB(input)

    for clause in kb.definite_clauses:
        print(clause)



if __name__ == "__main__":
    main()
