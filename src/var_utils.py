"""Utilities for variable analysis."""

from typing import Tuple
from src.ast_nodes import *
from src.ast_walker import walk


def collect_program_variables(program: Program) -> set[str]:
    variables = set()
    for node in walk(program, skip=[SubroutineDef]):
        match node:
            case Assignment(name=name):
                variables.add(name)
            case Var(name=name):
                variables.add(name)
    return variables

def collect_subroutine_local_variables(subroutine: SubroutineDef) -> set[str]:
    params = set(subroutine.params)
    all = set()
    for node in walk(subroutine):
        match node:
            case Assignment(name=name):
                all.add(name)
            case Var(name=name):
                all.add(name)
    body = all - params
    return body
