from abc import ABC,abstractmethod

class Predicate(ABC):
    
    args: tuple

    @property
    @abstractmethod
    def arity(self) -> int:
        pass

    def __init__(self, *args):
        if len(args) != self.arity:
            raise ValueError(
                f"{self.__class__.__name__} expects {self.arity} args, got {len(args)}"
            )
        self.args = args
    
    def __eq__(self,other:'Predicate'):
        return type(self) == type(other) and self.args == other.args

    def __hash__(self):
        return hash((type(self), self.args))
    
    def __repr__(self):
        args_str = ", ".join(map(str, self.args))
        return f"{self.__class__.__name__}({args_str})"

# Val(i, j, v)
class Val(Predicate):
    @property
    def arity(self):
        return 3

# Given(i, j, v)
class Given(Predicate):
    @property
    def arity(self):
        return 3
    
# LessH(i, j)
class LessH(Predicate):
    @property
    def arity(self):
        return 2
    
# GreaterH(i, j)
class GreaterH(Predicate):
    @property
    def arity(self):
        return 2
    
# LessV(i ,j)
class LessV(Predicate):
    @property
    def arity(self):
        return 2
    
# GreaterV(i, j)
class GreaterV(Predicate):
    @property
    def arity(self):
        return 2

# Less(v1, v2)
class Less(Predicate):
    @property
    def arity(self):
        return 2

def main():
    test = GreaterV(1,1)
    print(hash(test))

if __name__ == "__main__":
    main()