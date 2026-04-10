from fol.Predicate import *

class Literal:
    predicate: Predicate
    isNegative: bool # 0: False, 1: True

    def __init__(self, predicate: Predicate, isNegative: bool = False):
        self.predicate = predicate
        self.isNegative = isNegative
    
    # Trả về Literal Phủ định
    def negate(self)->'Literal':
        return Literal(self.predicate, (not self.isNegative))
    
    def __eq__(self,other:'Literal'):
        return type(self) == type(other) and self.predicate == other.predicate and self.isNegative == other.isNegative

    def __hash__(self):
        return hash((self.predicate, self.isNegative))
    
    def __repr__(self):
        return f"{'¬' if self.isNegative else ''}{self.predicate.__repr__()}"
    
def main():
    predicate = GreaterV(1,1)
    literal = Literal(predicate,False)
    negLiteral = literal.negate()
    print(negLiteral)

if __name__ == "__main__":
    main()
    