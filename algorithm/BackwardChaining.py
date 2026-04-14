from fol.KnowledgeBase import KnowledgeBase
from fol.Literal import Literal

class BackwardChainingSolver:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def ask(self, goal: Literal, visited: set = None, depth: int = 0) -> bool:
        if visited is None:
            visited = set()
        indent = "  " * depth

        if goal in visited:
            return False
        
        visited.add(goal)
        print(f"{indent}Goal: {goal}")

        # Base case 1: Goal đã là một fact có sẵn trong KB
        if goal in self.kb.facts:
            print(f"{indent}Goal '{goal}' is proven. (Found in facts)")
            visited.remove(goal)
            return True

        for clause in self.kb.definite_clauses:
            if clause.conclusion == goal:
                print(f"{indent}Trying to prove goal using clause: {clause}")
                condition_satisfy = True
                
                for condition in clause.conditions:
                    print(f"{indent}Sub-goal required: {condition}")
                    if not self.ask(condition, visited, depth + 1):
                        condition_satisfy = False
                        print(f"{indent}Sub-goal '{condition}' is not proven. Clause fails.")
                        break
                
                if condition_satisfy:
                    print(f"{indent}Goal '{goal}' is proven. (All sub-goals satisfied)")
                    visited.remove(goal)
                    return True

        print(f"{indent}Goal '{goal}' is not proven. (No matching rules or facts)")
        visited.remove(goal)
        return False

    def solve_cell(self, i: int, j: int, N: int) -> int:
        """
        Dùng backward chaining để truy vấn giá trị Val(i, j, v) cho một ô.
        """
        from fol.Predicate import Val
        
        print(f"\n--- Querying cell ({i}, {j}) using Backward Chaining ---")
        
        for v in range(1, N + 1):
            print(f"\nTesting value {v}...")
            goal = Literal(Val(i, j, v))
            
            # Gọi ask với depth = 0
            if self.ask(goal, depth=0):
                print(f"\n=> Result: Cell ({i}, {j}) is proven to be {v}.")
                return v
                
        print(f"\n=> Result: Cannot prove any value for cell ({i}, {j}).")
        return 0