import numpy as np

from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.Code.QuantumCode.MajoranaCode import MajoranaCode
from extendedstim.Code.QuantumCode.QuantumCSSCode import QuantumCSSCode
from extendedstim.Math.BinaryArray import BinaryArray as ba
from extendedstim.Physics.MajoranaOperator import MajoranaOperator


class MajoranaCSSCode(MajoranaCode, QuantumCSSCode):

    # %%  USER：构造方法
    def __init__(self, generators_x, generators_z, physical_number):
        QuantumCSSCode.__init__(self, generators_x, generators_z, physical_number)

    # %%  USER：属性方法
    ##  USER：求码距
    @property
    def distance(self):
        return ba.distance(self.check_matrix_x,'random')

    ##  USER：求码距（x方向）
    @property
    def distance_x(self):
        return ba.distance(self.check_matrix_x,'mip')

    ##  USER：求码距（z方向）
    @property
    def distance_z(self):
        return ba.distance(self.check_matrix_z,'mip')

    ##  USER：求逻辑算符（x方向）
    @property
    def logical_operators_x(self):
        matrix = self.check_matrix_x
        codewords = matrix.null_space
        independent_null_basis_list = []
        for vec in codewords:
            rank_before = matrix.rank
            matrix = ba.vstack(matrix, vec)
            if matrix.rank == rank_before + 1:
                independent_null_basis_list.append(vec)
        basis_list = ba.orthogonalize(independent_null_basis_list)
        majorana_logical_operators_x = []
        majorana_logical_operators_z = []
        for i in range(len(basis_list)):
            occupy=np.where(basis_list[i]==1)[0]
            temp = MajoranaOperator.HermitianOperatorFromOccupy(occupy,[])
            majorana_logical_operators_x.append(temp)
            temp = MajoranaOperator.HermitianOperatorFromOccupy([],occupy)
            majorana_logical_operators_z.append(temp)
        self._logical_operators_x = np.array(majorana_logical_operators_x, dtype=MajoranaOperator)
        self._logical_operators_z = np.array(majorana_logical_operators_z, dtype=MajoranaOperator)
        return self._logical_operators_x

    ##  USER：求逻辑算符（z方向）
    @property
    def logical_operators_z(self):
        _=self._logical_operators_x
        return self._logical_operators_z

    #%%  USER：静态方法
    @staticmethod
    def FromCheckMatrix(check_matrix):
        generators_x = []
        generators_z = []
        for i in range(len(check_matrix)):
            generators_x.append(MajoranaOperator.HermitianOperatorFromVector(check_matrix[i][0::2]))
            generators_z.append(MajoranaOperator.HermitianOperatorFromVector(check_matrix[i][1::2]))
        physical_number=check_matrix.shape[1]
        return MajoranaCSSCode(generators_x, generators_z, physical_number)

    @staticmethod
    def FromLinearCode(linear_code):
        assert isinstance(linear_code,LinearCode)
        generators_x = []
        generators_z = []
        check_matrix=linear_code.check_matrix
        for i in range(len(check_matrix)):
            occupy=check_matrix[i].occupy
            generators_x.append(MajoranaOperator.HermitianOperatorFromOccupy(occupy,[]))
            generators_z.append(MajoranaOperator.HermitianOperatorFromOccupy([],occupy))
        physical_number=check_matrix.shape[1]
        return MajoranaCSSCode(generators_x, generators_z, physical_number)
