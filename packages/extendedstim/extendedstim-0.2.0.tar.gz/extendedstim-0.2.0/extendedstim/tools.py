import numpy as np
from extendedstim.Physics.Operator import Operator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.Physics.MajoranaOperator import MajoranaOperator


def isinteger(num):
    return isinstance(num, (int, float, np.int32, np.int64,np.int8,np.int16))


def islist(num):
    return isinstance(num, (list, tuple, np.ndarray))


def isoperator(op):
    return isinstance(op,(Operator,PauliOperator,MajoranaOperator))