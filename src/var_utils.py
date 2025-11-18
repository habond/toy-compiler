"""Utilities for variable analysis.

This module provides functions for analyzing variable usage in toy language programs.
It helps the compiler determine which variables need stack allocation by walking the
AST and collecting variable names from assignments and references.

The variable collection is scope-aware:
- Program variables: Collects variables from the main program, excluding subroutines
- Subroutine local variables: Collects variables from subroutine bodies, excluding parameters

These utilities are essential for the compiler's stack frame setup, as they determine
how much stack space to allocate and which offsets to assign to each variable.
"""

from src.ast_nodes import *
from src.ast_walker import walk


def collect_program_variables(program: Program) -> set[str]:
    """Collect all variables used in the main program scope.

    This function walks the program AST and collects all variable names that appear
    in assignments or variable references. It excludes variables from subroutine
    definitions, as those are in separate scopes with their own stack frames.

    The function collects variables from:
    - Assignment statements (left-hand side variable names)
    - Variable references (in expressions)

    Args:
        program: The Program AST node representing the entire program.

    Returns:
        A set of variable names (strings) used in the main program scope.
        The set is unordered, as variable allocation order is determined elsewhere.

    Example:
        For a program like:
            x = 10;
            y = x + 5;
            println(y);

        This returns {"x", "y"} - both variables that need stack allocation.

    Note:
        - Variables are collected from both assignments and references to ensure
          all used variables are allocated (even if only read, not written)
        - Subroutines are skipped (via walk's skip parameter) since they have
          their own stack frames
        - Duplicate variable names naturally collapse into the set
    """
    variables = set()

    # Walk the AST, skipping subroutine definitions (they have separate scopes)
    for node in walk(program, skip=[SubroutineDef]):
        match node:
            case Assignment(name=name):
                # Variable being assigned to (e.g., "x" in "x = 5;")
                variables.add(name)
            case Var(name=name):
                # Variable being referenced (e.g., "x" in "y = x + 1;")
                variables.add(name)

    return variables


def collect_subroutine_local_variables(subroutine: SubroutineDef) -> set[str]:
    """Collect local variables from a subroutine, excluding parameters.

    This function walks a subroutine's body and collects all variable names,
    then filters out parameters to get only the local variables. Local variables
    are those that need stack allocation within the subroutine's frame, while
    parameters are passed on the stack by the caller.

    The distinction is important for stack frame layout:
    - Parameters have positive rbp offsets (above the frame pointer)
    - Local variables have negative rbp offsets (below the frame pointer)

    Args:
        subroutine: The SubroutineDef AST node to analyze.

    Returns:
        A set of local variable names (strings) that need stack allocation,
        excluding the subroutine's parameters.

    Example:
        For a subroutine like:
            sub calculate(x, y) {
                result = x + y;
                temp = result * 2;
                return temp;
            }

        This returns {"result", "temp"} - the local variables.
        Parameters "x" and "y" are excluded since they're passed by the caller.

    Note:
        - This function walks the entire subroutine body (no skip parameter)
          since we want all variables within this scope
        - Both assignments and references are collected to ensure all variables
          used in the subroutine are accounted for
        - Parameters are identified from the subroutine's parameter list and
          removed from the result set
    """
    # Get parameter names as a set for efficient lookup
    params = set(subroutine.params)

    # Collect all variables used in the subroutine body
    all = set()
    for node in walk(subroutine):
        match node:
            case Assignment(name=name):
                # Variable being assigned to (could be parameter or local)
                all.add(name)
            case Var(name=name):
                # Variable being referenced (could be parameter or local)
                all.add(name)

    # Compute local variables by removing parameters from all variables
    # This gives us only the variables that need allocation in this frame
    body = all - params

    return body
