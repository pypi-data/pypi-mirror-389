class BasicMath:
    def add(self,a,b):
        return a+b
    
    def sub(self,a,b):
        return a-b
    
    def multi(self,a,b):
        return a*b
    
    def dev(self,a,b):
        if b==0:
            return ValueError("cant divisible by zero")
        return a/b
    