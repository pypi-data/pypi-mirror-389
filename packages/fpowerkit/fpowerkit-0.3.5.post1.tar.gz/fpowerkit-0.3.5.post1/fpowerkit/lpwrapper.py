from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Union


@dataclass
class _LPVar:
    name:str
    idx:int
    lb:Optional[float] = 0
    ub:Optional[float] = None
    x:Optional[float] = None  # Solution value

    def __add__(self, other):
        expr = _LPExpr()
        expr.add_term(self.idx, 1.0)
        if isinstance(other, _LPExpr):
            return expr + other
        elif isinstance(other, _LPVar):
            expr.add_term(other.idx, 1.0)
            return expr
        elif isinstance(other, (int, float)):
            expr.add_const(other)
            return expr
        else:
            raise TypeError("Unsupported type for addition")
    
    def __sub__(self, other):
        expr = _LPExpr()
        expr.add_term(self.idx, 1.0)
        if isinstance(other, _LPExpr):
            return expr - other
        elif isinstance(other, _LPVar):
            expr.add_term(other.idx, -1.0)
            return expr
        elif isinstance(other, (int, float)):
            expr.add_const(-other)
            return expr
        else:
            raise TypeError("Unsupported type for subtraction")
    
    def __neg__(self):
        expr = _LPExpr()
        expr.add_term(self.idx, -1.0)
        return expr
    
    def __mul__(self, scalar:Union[float, int]):
        expr = _LPExpr()
        expr.add_term(self.idx, scalar)
        return expr
    
    def __rmul__(self, scalar:Union[float, int]):
        return self.__mul__(scalar)
    
    def __div__(self, scalar:Union[float, int]):
        expr = _LPExpr()
        expr.add_term(self.idx, 1.0 / scalar)
        return expr

class _LPEqCons: # expr == 0
    def __init__(self, expr:'_LPExpr'):
        self.expr = expr
        self.rhs = -self.expr.const
        self.expr.const = 0

class _LPIneqCons: # expr <= 0
    def __init__(self, expr:'_LPExpr'):
        self.expr = expr
        self.rhs = -self.expr.const
        self.expr.const = 0

class _LPExpr:
    def __init__(self):
        self.terms:Dict[int, float] = {}  # var_idx -> coefficient
        self.const = 0.0
    
    def add_term(self, var_idx:int, coeff:float):
        if var_idx in self.terms:
            self.terms[var_idx] += coeff
        else:
            self.terms[var_idx] = coeff
    
    def add_const(self, value:float):
        self.const += value
    
    def __add__(self, other):
        result = deepcopy(self)
        
        if isinstance(other, _LPExpr):
            for var_idx, coeff in other.terms.items():
                result.add_term(var_idx, coeff)
            result.add_const(other.const)
        elif isinstance(other, _LPVar):
            result.add_term(other.idx, 1.0)
        elif isinstance(other, (int, float)):
            result.add_const(other)
        else:
            raise TypeError("Unsupported type for addition")
        return result
    
    def __radd__(self, other):
        return self.__add__(other)
        
    def __sub__(self, other):
        result = deepcopy(self)
        
        if isinstance(other, _LPExpr):
            for var_idx, coeff in other.terms.items():
                result.add_term(var_idx, -coeff)
            result.add_const(-other.const)
        elif isinstance(other, _LPVar):
            result.add_term(other.idx, -1.0)
        elif isinstance(other, (int, float)):
            result.add_const(-other)
        else:
            raise TypeError("Unsupported type for subtraction")
        return result
    
    def __rsub__(self, other):
        if isinstance(other, _LPExpr):
            return other - self
        elif isinstance(other, _LPVar):
            result = _LPExpr()
            result.add_term(other.idx, 1.0)
        elif isinstance(other, (int, float)):
            result = _LPExpr()
            result.add_const(other)
        else:
            raise TypeError("Unsupported type for subtraction")
        
        return result - self
    
    def __neg__(self):
        result = deepcopy(self)
        for var_idx in result.terms:
            result.terms[var_idx] = -result.terms[var_idx]
        result.const = -result.const
        return result
    
    def __mul__(self, scalar:Union[float, int]):
        result = deepcopy(self)
        for var_idx in result.terms:
            result.terms[var_idx] *= scalar
        result.const *= scalar
        return result
    
    def __rmul__(self, scalar:Union[float, int]):
        return self.__mul__(scalar)
    
    def __div__(self, scalar:Union[float, int]):
        result = deepcopy(self)
        for var_idx in result.terms:
            result.terms[var_idx] /= scalar
        result.const /= scalar
        return result
    
    def __eq__(self, other):
        return _LPEqCons(self - other)
    
    def __le__(self, other):
        return _LPIneqCons(self - other)
    
    def __ge__(self, other):
        return _LPIneqCons(other - self)

def quicksum(items:Iterable[Union[_LPVar, _LPExpr]]) -> _LPExpr:
    result = _LPExpr()
    for other in items:
        if isinstance(other, _LPExpr):
            for var_idx, coeff in other.terms.items():
                result.add_term(var_idx, coeff)
            result.add_const(other.const)
        elif isinstance(other, _LPVar):
            result.add_term(other.idx, 1.0)
        elif isinstance(other, (int, float)):
            result.add_const(other)
        else:
            raise TypeError("Unsupported type for addition")
    return result

class LinProgProblem:
    def __init__(self):
        self.__vars:List[_LPVar] = []
        self.__eqs:List[_LPEqCons] = []
        self.__ineqs:List[_LPIneqCons] = []
        self.objective:_LPExpr = _LPExpr()
    
    def add_var(self, name:str, lb:Optional[float] = 0, ub: Optional[float] = None):
        """
            Add a variable to the linear programming problem.
            name: Name of the variable
            lb: Lower bound of the variable
            ub: Upper bound of the variable
        """
        idx = len(self.__vars)
        v = _LPVar(name, idx, lb, ub)
        self.__vars.append(v)
        return v
    
    def add_cons(self, cons:Union[_LPEqCons, _LPIneqCons, bool]):
        """
        Add a constraint to the linear programming problem.
            cons: The constraint to add (either equality or inequality)
        """
        if isinstance(cons, _LPEqCons):
            self.__eqs.append(cons)
        elif isinstance(cons, _LPIneqCons):
            self.__ineqs.append(cons)
        elif isinstance(cons, bool):
            if not cons:
                raise ValueError("Infeasible constraint (False) added to the problem")
        else:
            raise TypeError("Unsupported constraint type")
    
    def set_objective(self, expr:Union[int, float, _LPExpr]):
        """
        Set the objective function for the linear programming problem.
        """
        if isinstance(expr, (int, float)):
            expr_obj = _LPExpr()
            expr_obj.add_const(expr)
            self.objective = expr_obj
        else:
            self.objective = expr

    def solve(self, minimize:bool = True):
        """
        Solve the linear programming problem.
            minimize: If True, minimize the objective; if False, maximize it.
        Returns: (status_code:int, objective_value:float)
            status_code: 0 if successful, non-zero otherwise.
            objective_value: The optimal objective value if successful, 0.0 otherwise.
        """
        obj = self.objective
        if not minimize:
            obj = -obj
        try:
            from scipy.optimize import linprog
            import numpy as np
        except Exception as e:
            raise RuntimeError("scipy.optimize.linprog is required") from e

        # objective coefficients
        n = len(self.__vars)
        c = np.zeros(n)
        for var_idx, coeff in obj.terms.items():
            c[var_idx] = coeff

        # variable bounds (None means unbounded for linprog)
        bounds = [(v.lb, v.ub) for v in self.__vars]

        # equality constraints
        m1 = len(self.__eqs)
        if m1 > 0:
            A_eq = np.zeros((m1, n))
            b_eq = np.zeros(m1)
            for i, eq in enumerate(self.__eqs):
                for var_idx, coeff in eq.expr.terms.items():
                    A_eq[i, var_idx] = coeff
                b_eq[i] = eq.rhs
        else:
            A_eq = None
            b_eq = None

        # inequality constraints (A_ub x <= b_ub)
        m2 = len(self.__ineqs)
        if m2 > 0:
            A_ub = np.zeros((m2, n))
            b_ub = np.zeros(m2)
            for i, ineq in enumerate(self.__ineqs):
                for var_idx, coeff in ineq.expr.terms.items():
                    A_ub[i, var_idx] = coeff
                b_ub[i] = ineq.rhs
        else:
            A_ub = None
            b_ub = None

        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        if not res.success:
            return res.status, 0.0
        
        for i, v in enumerate(self.__vars):
            v.x = res.x[i]
            
        return res.status, float(res.fun) + obj.const