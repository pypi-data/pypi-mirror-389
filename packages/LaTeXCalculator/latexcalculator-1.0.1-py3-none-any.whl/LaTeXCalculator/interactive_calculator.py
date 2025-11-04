from .calculator import *
from rich.panel import Panel

app = LaTeXExpressionCalculatorApp()

def interactive_calculator():
    """
    Interactive calculator.
    """
    
    console.print(Panel(
        title="LaTeX Interactive Calculator",
        renderable="""\
enter 'quit' to exit
enter 'help' to view help
enter 'calc' to enter calculation mode
enter 'solve' to enter equation solving mode
enter 'derivative' to calculate derivative
enter 'integral' to calculate integral
enter 'limit' to calculate limit""",
        border_style="green"
    ))

    while True:
        user_input = console.input("\n[green]Command> [/green]").strip().lower()
        
        if user_input == 'quit':
            print("Goodbye!")
            break
        elif user_input == 'help':
            _print_interactive_calculator_help()
        elif user_input == 'calc':
            _calculation_mode()
        elif user_input == 'solve':
            _equation_solving_mode()
        elif user_input == 'derivative':
            _derivative_mode()
        elif user_input == 'integral':
            _integral_mode()
        elif user_input == 'limit':
            _limit_mode()
        else:
            print("Invalid command. Please enter 'help', 'calc', 'solve', 'derivative', 'integral', 'limit', or 'quit'.")


def _calculation_mode():
    console.print(Panel(
        title="Calculation Mode",
        renderable="Enter 'quit' to return to Command mode\nEnter LaTeX expressions to calculate",
        border_style="yellow"
    ))
    
    while True:
        user_input = console.input("\n[yellow]LaTeX> [/yellow]").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Returning to Command mode...")
            break
        
        try:
            result = app.calculate(user_input)
            console.print(f"Result: {result['result']}")
            if result['latex_result']:
                console.print(f"LaTeX: {result['latex_result']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _equation_solving_mode():
    console.print(Panel(
        title="Equation Solving Mode",
        renderable="Enter 'quit' to return to Command mode\nEnter equations to solve (use commas for systems)",
        border_style="yellow"
    ))
    
    while True:
        user_input = console.input("\n[yellow]Equation> [/yellow]").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Returning to Command mode...")
            break
        
        try:
            if ',' in user_input:
                equations = [eq.strip() for eq in user_input.split(',')]
                result = app.solve_system(equations)
            else:
                result = app.solve_equation(user_input)
            
            if 'solutions' in result:
                console.print(f"Solutions: {result['solutions']}")
            if 'numeric_solutions' in result:
                console.print(f"Numeric solutions: {result['numeric_solutions']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _derivative_mode():
    console.print(Panel(
        title="Derivative Mode",
        renderable="Enter 'quit' to return to Command mode\nEnter expressions to differentiate (optionally specify variable: 'expr, var')",
        border_style="yellow"
    ))
    
    while True:
        user_input = console.input("\n[yellow]Derivative> [/yellow]").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Returning to Command mode...")
            break
        
        try:
            if ',' in user_input:
                expr, var = [x.strip() for x in user_input.split(',', 1)]
                result = app.calculate_derivative(expr, variable=var)
            else:
                result = app.calculate_derivative(user_input)
            
            console.print(f"Derivative: {result['derivative']}")
            console.print(f"LaTeX: {result['latex_result']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _integral_mode():
    console.print(Panel(
        title="Integral Mode",
        renderable="Enter 'quit' to return to Command mode\nEnter expressions to integrate (optionally specify variable: 'expr, var')",
        border_style="yellow"
    ))
    
    while True:
        user_input = console.input("\n[yellow]Integral> [/yellow]").strip() 
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Returning to Command mode...")
            break
        
        try:
            if ',' in user_input:
                expr, var = [x.strip() for x in user_input.split(',', 1)]
                result = app.calculate_integral(expr, variable=var)
            else:
                result = app.calculate_integral(user_input)
            
            console.print(f"Integral: {result['result']}")
            console.print(f"LaTeX: {result['latex_result']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _limit_mode():
    console.print(Panel(
        title="Limit Mode",
        renderable="Enter 'quit' to return to Command mode\nEnter expressions to find limit (optionally specify variable and point: 'expr, var, point')",
        border_style="yellow"
    ))
    
    while True:
        user_input = console.input("\n[yellow]Limit> [/yellow]").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Returning to Command mode...")
            break
        
        try:
            if ',' in user_input:
                parts = [x.strip() for x in user_input.split(',')]
                if len(parts) == 3:
                    expr, var, point = parts
                    result = app.calculate_limit(expr, variable=var, point=point)
                elif len(parts) == 2:
                    expr, var = parts
                    result = app.calculate_limit(expr, variable=var)
                else:
                    result = app.calculate_limit(parts[0])
            else:
                result = app.calculate_limit(user_input)
            
            console.print(f"Limit: {result['limit']}")
            console.print(f"LaTeX: {result['latex_result']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def _print_interactive_calculator_help():
    """
    Print help information.
    """
    combined_table = Table(
        title="Supported LaTeX Functions & Commands",
        header_style="bold",
        border_style="default"
    )
    combined_table.add_column("Category", style="cyan", justify="center")
    combined_table.add_column("Details", style="green", justify="right")
    combined_table.add_column("Example/Description", style="yellow", justify="left")

    combined_table.add_row("", "Arithmetic", "+, -, \\times, \\cdot, \\div")
    combined_table.add_row("", "Fractions", "\\frac{numerator}{denominator}")
    combined_table.add_row("", "Square Roots", "\\sqrt{expression}, \\sqrt[n]{expression}")
    combined_table.add_row("Supported", "Exponents", "^{exponent}")
    combined_table.add_row("LaTeX Syntax", "Functions", "\\sin, \\cos, \\tan, \\log, \\ln, \\exp, etc.")
    combined_table.add_row("", "Constants", "\\pi, \\e, \\infty")
    combined_table.add_row("", "Greek Letters", "\\alpha, \\beta, \\gamma, etc.")
    combined_table.add_row("", "Combinatorial Numbers", "\\binom{n}{k}", end_section=True)

    combined_table.add_row("Equation", "Single Equation", "x^2 - 4 = 0")
    combined_table.add_row("Solving", "System of Equations", "x + y = 5, x - y = 1 (use comma to separate equations)", end_section=True)

    combined_table.add_row("", "Derivative", "Input expression, optional variable (default x)")
    combined_table.add_row("Calculus", "Integral", "Input expression, optional variable (default x)")
    combined_table.add_row("", "Limit", "Input expression, optional variable and point (default x→0)", end_section=True)

    combined_table.add_row("", "help", "Display this help")
    combined_table.add_row("", "solve", "Enter equation solving mode")
    combined_table.add_row("", "calc", "Return to calculation mode")
    combined_table.add_row("Commands", "derivative", "Enter derivative mode")
    combined_table.add_row("", "integral", "Enter integral mode")
    combined_table.add_row("", "limit", "Enter limit mode")
    combined_table.add_row("", "quit", "Exit")

    console.print(combined_table, markup=False)