import re, math, rich.traceback
import sympy as sp
from sympy import symbols, sympify, latex, pi, E, I, oo
from sympy.parsing.latex import parse_latex
from typing import Union, Dict, Any, List
from rich.console import Console
from rich.table import Table

rich.traceback.install()
console = Console()

class LaTeXBase:
    """
    LaTex Calculator Base Class with shared functionalities and constants.
    """
    
    # pre-defined symbols and functions mapping
    SYMBOLS = {
        'pi': pi,
        'e': E,
        'i': I,
        'infty': oo,
    }

    FUNCTION_MAP = {
        'sin': sp.sin,
        'cos': sp.cos,
        'tan': sp.tan,
        'cot': sp.cot,
        'sec': sp.sec,
        'csc': sp.csc,
        'arcsin': sp.asin,
        'arccos': sp.acos,
        'arctan': sp.atan,
        'sinh': sp.sinh,
        'cosh': sp.cosh,
        'tanh': sp.tanh,
        'log': sp.log,
        'ln': sp.log,
        'exp': sp.exp,
        'sqrt': sp.sqrt,
        'abs': sp.Abs,
        'floor': sp.floor,
        'ceil': sp.ceiling,
        'factorial': sp.factorial,
        'gamma': sp.gamma,
        'binomial': sp.binomial,
    }

    CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'infty': float('inf'),
    }

    @staticmethod
    def preprocess_latex(latex_str: str) -> str:
        """
        Preprocess LaTeX string to make it recognizable by SymPy.
        """
        # check if the expression is empty
        if not latex_str.strip():
            raise ValueError("Empty expression")

        # remove spaces
        latex_str = latex_str.replace(' ', '')
        
        # step 1: handle special structures (fractions, square roots, binomials, etc.)
        
        # handle fractions \frac{a}{b} -> (a)/(b)
        while r'\frac{' in latex_str:
            match = re.search(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', latex_str)
            if match:
                numerator, denominator = match.groups()
                replacement = f'({numerator})/({denominator})'
                latex_str = latex_str[:match.start()] + replacement + latex_str[match.end():]
            else:
                break
        
        # step 2: handle square roots \sqrt{a} -> sqrt(a)
        while r'\sqrt{' in latex_str:
            match = re.search(r'\\sqrt\{([^{}]*)\}', latex_str)
            if match:
                content = match.group(1)
                replacement = f'sqrt({content})'
                latex_str = latex_str[:match.start()] + replacement + latex_str[match.end():]
            else:
                break
        
        # step 3: handle nth roots \sqrt[n]{a} -> (a)^(1/n)
        while r'\sqrt[' in latex_str:
            match = re.search(r'\\sqrt\[([^]]*)\]\{([^{}]*)\}', latex_str)
            if match:
                n, content = match.groups()
                replacement = f'({content})**(1/({n}))'
                latex_str = latex_str[:match.start()] + replacement + latex_str[match.end():]
            else:
                break
        
        # step 4: handle binomial coefficients \binom{a}{b} -> binomial(a, b)
        while r'\binom{' in latex_str:
            match = re.search(r'\\binom\{([^{}]*)\}\{([^{}]*)\}', latex_str)
            if match:
                n, k = match.groups()
                replacement = f'binomial({n}, {k})'
                latex_str = latex_str[:match.start()] + replacement + latex_str[match.end():]
            else:
                break
        
        # step 5: handle functions and special symbols (using direct string replacements, avoid regex)
        
        # handle functions - use simple string replacements
        function_mappings = [
            (r'\sin', 'sin'),
            (r'\cos', 'cos'),
            (r'\tan', 'tan'),
            (r'\cot', 'cot'),
            (r'\sec', 'sec'),
            (r'\csc', 'csc'),
            (r'\arcsin', 'arcsin'),
            (r'\arccos', 'arccos'),
            (r'\arctan', 'arctan'),
            (r'\sinh', 'sinh'),
            (r'\cosh', 'cosh'),
            (r'\tanh', 'tanh'),
            (r'\log', 'log'),
            (r'\ln', 'ln'),
            (r'\exp', 'exp'),
            (r'\sqrt', 'sqrt'),
            (r'\abs', 'abs'),
            (r'\lfloor', 'floor('),
            (r'\rfloor', ')'),
            (r'\lceil', 'ceil('),
            (r'\rceil', ')'),
        ]
        
        for latex_cmd, replacement in function_mappings:
            latex_str = latex_str.replace(latex_cmd, replacement)
        
        # step 6: handle Greek letters and special symbols
        symbol_mappings = [
            (r'\pi', 'pi'),
            (r'\infty', 'infty'),
            (r'\alpha', 'alpha'),
            (r'\beta', 'beta'),
            (r'\gamma', 'gamma'),
            (r'\delta', 'delta'),
            (r'\epsilon', 'epsilon'),
            (r'\zeta', 'zeta'),
            (r'\eta', 'eta'),
            (r'\theta', 'theta'),
            (r'\iota', 'iota'),
            (r'\kappa', 'kappa'),
            (r'\lambda', 'lambda'),
            (r'\mu', 'mu'),
            (r'\nu', 'nu'),
            (r'\xi', 'xi'),
            (r'\rho', 'rho'),
            (r'\sigma', 'sigma'),
            (r'\tau', 'tau'),
            (r'\upsilon', 'upsilon'),
            (r'\phi', 'phi'),
            (r'\chi', 'chi'),
            (r'\psi', 'psi'),
            (r'\omega', 'omega'),
        ]
        
        for latex_sym, replacement in symbol_mappings:
            latex_str = latex_str.replace(latex_sym, replacement)
        
        # step 7: handle operators and exponents
        
        # handle operators
        latex_str = latex_str.replace(r'\times', '*')
        latex_str = latex_str.replace(r'\cdot', '*')
        latex_str = latex_str.replace(r'\div', '/')
        
        # handle exponents (replace ^ with **)
        latex_str = latex_str.replace('^', '**')
        
        # step 8: handle implicit multiplication (add * only where needed)
        
        # between numbers and letters: 2x -> 2*x
        latex_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', latex_str)
        # between letters and numbers: x2 -> x*2
        latex_str = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', latex_str)
        # between right parenthesis and letters: )x -> )*x
        latex_str = re.sub(r'(\))([a-zA-Z])', r'\1*\2', latex_str)
        # between letters and left parenthesis: x( -> x*(
        latex_str = re.sub(r'([a-zA-Z])(\()', r'\1*\2', latex_str)
        
        # step 9: handle special parentheses
        latex_str = latex_str.replace(r'\left(', '(')
        latex_str = latex_str.replace(r'\right)', ')')
        latex_str = latex_str.replace(r'\left[', '[')
        latex_str = latex_str.replace(r'\right]', ']')
        latex_str = latex_str.replace(r'\left\{', '{')
        latex_str = latex_str.replace(r'\right\}', '}')
        
        return latex_str

    @staticmethod
    def extract_variables(expression_str: str) -> set:
        """
        Get all variables in the expression.
        """
        # remove numbers, operators, and function names
        cleaned = re.sub(r'\d+\.?\d*', '', expression_str)
        cleaned = re.sub(r'[+\-*/^()\[\],]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # remove protected symbols and function names
        protected = set(LaTeXBase.FUNCTION_MAP.keys()) | set(LaTeXBase.CONSTANTS.keys()) | {
            'pi', 'e', 'i', 'infty', 'alpha', 'beta', 'gamma', 'delta', 'epsilon',
            'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi',
            'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega'
        }
        
        # extract variables
        words = set(cleaned.split())
        variables = words - protected
        
        return variables

    @staticmethod
    def parse_latex_expression(latex_str: str, variable_values: Dict[str, float] = None) -> sp.Expr:
        """
        Parse a LaTeX expression into a SymPy expression.
        """
        if variable_values is None:
            variable_values = {}
        
        try:
            # method 1: use SymPy's LaTeX parser (if available)
            try:
                expr = parse_latex(latex_str)
                return expr
            except (ImportError, AttributeError, Exception) as e:
                # if SymPy's LaTeX parser fails, use custom method
                pass
            
            # method 2: custom preprocessing and parsing
            processed = LaTeXBase.preprocess_latex(latex_str)
            
            # extract variables
            variables = LaTeXBase.extract_variables(processed)
            
            # create symbols
            sympy_symbols = {var: symbols(var) for var in variables}
            
            # add predefined symbols
            sympy_symbols.update(LaTeXBase.SYMBOLS)
            
            # parse expression
            expr = sympify(processed, locals=sympy_symbols)
            
            # apply variable values
            if variable_values:
                substitution_dict = {}
                for var, value in variable_values.items():
                    if var in sympy_symbols:
                        substitution_dict[sympy_symbols[var]] = value
                expr = expr.subs(substitution_dict)
            
            return expr
            
        except Exception as e:
            raise ValueError(e)

    @staticmethod
    def evaluate_expression(expr: sp.Expr, numeric: bool = True) -> Union[sp.Expr, float, complex]:
        """
        Evaluate the expression.
        """
        try:
            if numeric:
                # numerical evaluation
                result = expr.evalf(chop=True)
                if result.is_real:
                    result = float(result)
                    return int(result) if result == int(result) else result
                elif result.is_complex:
                    return complex(result)
                else:
                    return result
            else:
                # symbolic evaluation (simplification)
                return sp.simplify(expr)
        except Exception as e:
            raise ValueError(f"Can't evaluate expression: {e}")

class LaTeXExpressionCalculator(LaTeXBase):
    """
    LaTeX expression calculator class.
    """
    
    def __init__(self):
        self.variable_values = {}
    
    def set_variables(self, variable_values: Dict[str, float]):
        """
        Set variable values.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``variable_values``
             - A dictionary of variable names and their values.
        """
        self.variable_values = variable_values
    
    def add_variable(self, name: str, value: float):
        """
        Add a single variable.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``name``
             - Variable name
           * - ``value``
             - Variable value
        """
        self.variable_values[name] = value
    
    def calculate(self, latex_str: str, return_type: str = 'auto') -> Dict[str, Any]:
        """
        Calculate the LaTeX expression.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_str``
             - LaTeX string
           * - ``return_type``
             - Return type (``'auto'``, ``'numeric'``, ``'symbolic'``).
        
        **RETURNS**

        A dictionary containing the result and detailed information.
        """
        try:
            # parse the LaTeX expression
            expr = self.parse_latex_expression(latex_str, self.variable_values)
            
            # evaluate the expression
            if return_type == 'symbolic':
                result = self.evaluate_expression(expr, numeric=False)
                result_type = 'symbolic'
            elif return_type == 'numeric':
                result = self.evaluate_expression(expr, numeric=True)
                result_type = 'numeric'
            else:  # auto
                try:
                    # check if the expression contains symbols
                    if hasattr(expr, 'free_symbols') and expr.free_symbols:
                        result = self.evaluate_expression(expr, numeric=False)
                        result_type = 'symbolic'
                    else:
                        result = self.evaluate_expression(expr, numeric=True)
                        result_type = 'numeric'
                except:
                    result = self.evaluate_expression(expr, numeric=False)
                    result_type = 'symbolic'
            
            # generate the result dictionary
            response = {
                'input': latex_str,
                'parsed_expression': str(expr),
                'result': result,
                'result_type': result_type,
                'latex_result': latex(expr) if hasattr(expr, 'free_symbols') and expr.free_symbols else None,
            }
                
            # add additional information
            if hasattr(expr, 'free_symbols'):
                response['free_variables'] = [str(sym) for sym in expr.free_symbols]
            else:
                response['free_variables'] = []
            
            return response
            
        except Exception as e:
            raise ArithmeticError(e) from None
    
    def calculate_multiple(self, expressions: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Calculate multiple LaTeX expressions.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``expressions``
             - A list of LaTeX strings
           * - ``return_type``
             - Return type (``'auto'``, ``'numeric'``, ``'symbolic'``).
        
        **RETURNS**
        
        A list of dictionaries containing the results and detailed information.
        """
        results = []
        for expr in expressions:
            results.append(self.calculate(expr, **kwargs))
        return results

class LaTeXEquationSolver(LaTeXBase):
    """
    LaTeX equation solver class.
    """
    
    def solve(self, latex_equation: str, variable: str = None) -> Dict[str, Any]:
        """
        Solve a LaTeX equation.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_equation``
             - LaTeX equation string
           * - ``variable``
             - Variable to solve for. If None, attempts to solve for all variables.
        
        **RETURNS**
        
        A dictionary containing the solutions and detailed information.
        """
        try:
            # split the equation into left and right sides
            if '=' in latex_equation:
                left, right = latex_equation.split('=', 1)
                processed_left = self.preprocess_latex(left.strip())
                processed_right = self.preprocess_latex(right.strip())
                equation_str = f"({processed_left}) - ({processed_right})"
            else:
                equation_str = self.preprocess_latex(latex_equation.strip())
            
            # parse the LaTeX expression
            expr = self.parse_latex_expression(equation_str)
            
            # extract variables from the expression
            variables = self.extract_variables(str(expr))
            
            if variable is None:
                if len(variables) == 1:
                    variable = list(variables)[0]
                else:
                    raise ValueError(f"need to specify a variable to solve for. available variables: {list(variables)}") from None
            
            if variable not in variables:
                raise ValueError(f"variable '{variable}' not found in the equation") from None
            
            # solve the equation
            var_symbol = symbols(variable)
            solutions = sp.solve(expr, var_symbol)
            
            # evaluate the solutions numerically
            numeric_solutions = []
            for sol in solutions:
                try:
                    numeric_solutions.append(complex(sol.evalf()))
                except:
                    numeric_solutions.append(sol)
            
            return {
                'equation': latex_equation,
                'variable': variable,
                'solutions': solutions,
                'numeric_solutions': numeric_solutions,
                'number_of_solutions': len(solutions)
            }
            
        except Exception as e:
            raise ArithmeticError(e) from None

class LaTeXSystemSolver(LaTeXBase):
    """
    LaTeX system solver class.
    """
    
    def solve(self, equations: List[str], variables: List[str] = None) -> Dict[str, Any]:
        """
        Solve a system of LaTeX equations.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``equations``
             - A list of LaTeX strings representing the equations
           * - ``variables``
             - A list of variables to solve for. If None, attempts to solve for all variables.
        
        **RETURNS**
        
        A dictionary containing the solutions and detailed information.
        """
        try:
            processed_eqs = []
            all_variables = set()
            
            for eq in equations:
                if '=' in eq:
                    left, right = eq.split('=', 1)
                    processed_left = self.preprocess_latex(left.strip())
                    processed_right = self.preprocess_latex(right.strip())
                    equation_str = f"({processed_left}) - ({processed_right})"
                else:
                    equation_str = self.preprocess_latex(eq.strip())
                
                expr = self.parse_latex_expression(equation_str)
                processed_eqs.append(expr)
                all_variables.update(self.extract_variables(str(expr)))
            
            if variables is None:
                variables = list(all_variables)
            
            # create sympy variables
            sympy_vars = [symbols(var) for var in variables]
            
            # solve the system of equations
            solutions = sp.solve(processed_eqs, sympy_vars)
            
            return {
                'equations': equations,
                'variables': variables,
                'solutions': solutions
            }
            
        except Exception as e:
            raise ArithmeticError(e) from None

class LaTeXIntegralCalculator(LaTeXBase):
    """
    LaTeX integral calculator class.
    """
    
    def calculate(self, latex_integral: str, variable: str = 'x') -> Dict[str, Any]:
        """
        Calculate the integral of a LaTeX expression.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_integral``
             - The LaTeX string representing the integral to be calculated.
           * - ``variable``
             - The variable of integration. Default is ``'x'``.
        
        **RETURNS**
        
        A dictionary containing the result of the integral and detailed information.
        """
        try:
            # parse the integral expression
            expr = self.parse_latex_expression(latex_integral)
            
            # calculate the integral
            var_symbol = symbols(variable)
            integral_result = sp.integrate(expr, var_symbol)
            
            return {
                'integral': latex_integral,
                'variable': variable,
                'result': integral_result,
                'latex_result': latex(integral_result)
            }
            
        except Exception as e:
            raise ArithmeticError(e) from None

class LaTeXDerivativeCalculator(LaTeXBase):
    """
    LaTeX derivative calculator class.
    """
    
    def calculate(self, latex_expression: str, variable: str = 'x', n: int = 1) -> Dict[str, Any]:
        """
        Calculate the derivative of a LaTeX expression.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_expression``
             - The LaTeX string representing the expression to be differentiated.
           * - ``variable``
             - The variable with respect to which the derivative is to be computed. Default is ``'x'``.
           * - ``n``
             - The order of the derivative. Default is ``1``.
        
        **RETURNS**
        
        A dictionary containing the result of the derivative and detailed information.
        """
        try:
            # parse the expression
            expr = self.parse_latex_expression(latex_expression)
            
            # calculate the derivative
            var_symbol = symbols(variable)
            derivative = sp.diff(expr, var_symbol, n)
            
            return {
                'expression': latex_expression,
                'variable': variable,
                'order': n,
                'derivative': derivative,
                'latex_result': latex(derivative)
            }
            
        except Exception as e:
            raise ArithmeticError(e) from None

class LaTeXLimitCalculator(LaTeXBase):
    """
    LaTeX limit calculator class.
    """
    
    def calculate(self, latex_expression: str, variable: str = 'x', point: str = '0') -> Dict[str, Any]:
        """
        Calculate the limit of a LaTeX expression.
        
        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_expression``
             - The LaTeX string representing the expression to be limited.
           * - ``variable``
             - The variable with respect to which the limit is to be computed. Default is ``'x'``.
           * - ``point``
             - The point at which the limit is to be computed. Default is ``'0'``.
        
        **RETURNS**
        
        A dictionary containing the result of the limit and detailed information.
        """
        try:
            # parse the expression and point
            expr = self.parse_latex_expression(latex_expression)
            point_expr = self.parse_latex_expression(point)
            
            # calculate the limit
            var_symbol = symbols(variable)
            limit_result = sp.limit(expr, var_symbol, point_expr)
            
            return {
                'expression': latex_expression,
                'variable': variable,
                'point': point,
                'limit': limit_result,
                'latex_result': latex(limit_result)
            }
            
        except Exception as e:
            raise ArithmeticError(e) from None

class LaTeXExpressionCalculatorApp:
    """
    LaTeX expression calculator application class, integrating all features.
    """
    
    def __init__(self):
        self.calculator = LaTeXExpressionCalculator()
        self.equation_solver = LaTeXEquationSolver()
        self.system_solver = LaTeXSystemSolver()
        self.integral_calculator = LaTeXIntegralCalculator()
        self.derivative_calculator = LaTeXDerivativeCalculator()
        self.limit_calculator = LaTeXLimitCalculator()
    
    def set_variables(self, variable_values: Dict[str, float]):
        """
        Set variable values (used for expression evaluation).

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``variable_values``
             - A dictionary mapping variable names to their values.
        """
        self.calculator.set_variables(variable_values)
    
    def calculate(self, latex_str: str, **kwargs):
        """
        Calculate the expression.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``latex_str``
             - The LaTeX string representing the expression to be computed.
        
        **RETURNS**
        
        A dictionary containing the result of the expression evaluation and detailed information.
        """
        return self.calculator.calculate(latex_str, **kwargs)
    
    def solve_equation(self, equation: str, **kwargs):
        """
        Solve the equation.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``equation``
             - The LaTeX string representing the equation to be solved.
        
        **RETURNS**
        
        A dictionary containing the result of the equation solving and detailed information.
        """
        return self.equation_solver.solve(equation, **kwargs)
    
    def solve_system(self, equations: List[str], **kwargs):
        """
        Solve the system of equations.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``equations``
             - A list of LaTeX strings representing the equations in the system.
        
        **RETURNS**
        
        A dictionary containing the result of the system solving and detailed information.
        """
        return self.system_solver.solve(equations, **kwargs)
    
    def calculate_integral(self, integral: str, **kwargs):
        """
        Calculate the integral.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``integral``
             - The LaTeX string representing the integral to be computed.
        
        **RETURNS**
        
        A dictionary containing the result of the integral computing and detailed information.
        """
        return self.integral_calculator.calculate(integral, **kwargs)
    
    def calculate_derivative(self, expression: str, **kwargs):
        """
        Calculate the derivative.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``expression``
             - The LaTeX string representing the expression to be differentiated.
        
        **RETURNS**
        
        A dictionary containing the result of the derivative computing and detailed information.
        """
        return self.derivative_calculator.calculate(expression, **kwargs)
    
    def calculate_limit(self, expression: str, **kwargs):
        """
        Calculate the limit.

        **PARAMETERS**

        .. list-table::
           :widths: 30 70

           * - ``expression``
             - The LaTeX string representing the expression to be limited.
        
        **RETURNS**
        
        A dictionary containing the result of the limit computing and detailed information.
        """
        return self.limit_calculator.calculate(expression, **kwargs)
