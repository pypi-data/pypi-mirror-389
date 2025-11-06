import numpy as np
from extendedstim.Code.QuantumCode.PauliCode import PauliCode
from extendedstim.Code.QuantumCode.QuantumCSSCode import QuantumCSSCode
from extendedstim.Math.BinaryArray import BinaryArray as ba
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator


class PauliCSSCode(PauliCode, QuantumCSSCode):

    # %%  USER：构造方法
    def __init__(self, generators_x, generators_z, physical_number):
        QuantumCSSCode.__init__(self, generators_x, generators_z, physical_number)

    # %%  USER：属性方法
    ##  TODO：求Pauli CSS code的距离（x方向）
    @property
    def distance_x(self):
        return 1

    ##  TODO：求Pauli CSS code的距离（z方向）
    @property
    def distance_z(self):
        return 1

    ##  TODO：求Pauli CSS code的逻辑算子（x方向）
    @property
    def logical_operators_x(self):
        if self._logical_operators_x is not None:
            return self._logical_operators_x
        else:
            raise NotImplementedError('这个功能还没有实现')

    ##  TODO：求Pauli CSS code的逻辑算子（z方向）
    @property
    def logical_operators_z(self):
        if self._logical_operators_z is not None:
            return self._logical_operators_z
        else:
            raise NotImplementedError('这个功能还没有实现')

    @staticmethod
    def SteaneCode():
        generators_x = [PauliOperator([3,4,5,6],[],1),PauliOperator([1,2,5,6],[],1),PauliOperator([0,2,4,6],[],1)]
        generators_z = [PauliOperator([],[3,4,5,6],1),PauliOperator([],[1,2,5,6],1),PauliOperator([],[0,2,4,6],1)]
        physical_number=7
        result=PauliCSSCode(generators_x, generators_z, physical_number)
        result._logical_operators_x=[PauliOperator([0,1,2],[],1)]
        result._logical_operators_z=[PauliOperator([],[0,1,2],1)]

    @staticmethod
    def SurfaceCode(d):
        generators_x=[]
        generators_z=[]
        if d==3:
            generators_x=[
                PauliOperator([6,7],[],1),
                PauliOperator([4,5,7,8],[],1),
                PauliOperator([0,1,3,4],[],1),
                PauliOperator([1,2],[],1)
            ]
            generators_z=[
                PauliOperator([],[3,4,6,7],1),
                PauliOperator([],[5,8],1),
                PauliOperator([],[0,3],1),
                PauliOperator([],[1,2,4,5],1)
            ]
            physical_number=9
            result=PauliCSSCode(generators_x, generators_z, physical_number)
            result._logical_operators_x=[PauliOperator([0,3,6],[],1)]
            result._logical_operators_z=[PauliOperator([],[0,1,2],1)]
        return result
