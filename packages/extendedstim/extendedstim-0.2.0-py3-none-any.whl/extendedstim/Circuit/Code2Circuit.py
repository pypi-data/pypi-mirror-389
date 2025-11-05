import numpy as np
from extendedstim.Circuit.Circuit import Circuit
from extendedstim.Code.QuantumCode.MajoranaCSSCode import MajoranaCSSCode
from extendedstim.Code.QuantumCode.PauliCSSCode import PauliCSSCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator


#%%  USER：===将量子码转换为量子线路===
def Code2Circuit(code,p_noise,p_measure,noise_model,cycle_number):
    if noise_model=='phenomenological':
        if isinstance(code,MajoranaCSSCode):
            return MajoranaCSSCode2PhenomenologicalCircuit(code,p_noise,p_measure,cycle_number)
        elif isinstance(code,PauliCSSCode):
            return PauliCSSCode2PhenomenologicalCircuit(code,p_noise,p_measure,cycle_number)
        else:
            raise NotImplementedError
    elif noise_model=='circuit-level':
        if isinstance(code,MajoranaCSSCode):
            return MajoranaCSSCode2CircuitLevelCircuit(code,p_noise,p_measure,cycle_number)
        elif isinstance(code,PauliCSSCode):
            return PauliCSSCode2CircuitLevelCircuit(code,p_noise,p_measure,cycle_number)
        else:
            raise NotImplementedError
    elif noise_model=='code-capacity':
        if isinstance(code,MajoranaCSSCode):
            return MajoranaCSSCode2CodeCapacityCircuit(code,p_noise,p_measure,cycle_number)
        elif isinstance(code,PauliCSSCode):
            return PauliCSSCode2CodeCapacityCircuit(code,p_noise,p_measure,cycle_number)
        else:
            raise NotImplementedError
    else:
        raise ValueError('noise_model must be phenomenological, circuit-level, or code-capacity')


#%%  KEY：将Majorana CSS code转换为现象级噪声下的测试线路
def MajoranaCSSCode2PhenomenologicalCircuit(code,p_noise,p_measure,cycle_number:int):

    ##  ===数据预处理===
    assert isinstance(code,MajoranaCSSCode)
    stabilizers_x=code.generators_x
    stabilizers_z=code.generators_z
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z

    ##  获取logical operators
    logical_occupy=[]
    for i in range(len(logical_x)):
        logical_occupy.append(1j*logical_x[i]@logical_z[i])

    majorana_number=code.physical_number
    stabilizer_number = len(stabilizers_x) + len(stabilizers_z)

    ##  ===生成线路===
    circuit_z = Circuit()
    circuit_z.append({"name":"FORCE","majorana_state":np.append(logical_occupy,np.append(stabilizers_x, stabilizers_z)),
                      'pauli_state':[PauliOperator([],[],1)]*(stabilizer_number+len(logical_occupy)),
                      'pauli_number':0,'majorana_number':majorana_number})

    ##  第一轮测量假设完美的初始化
    observable_include= []  # 记录可观测量的索引
    for i,logical_operator in enumerate(logical_occupy):
        circuit_z.append({"name":"MPP","target":logical_operator,"index":i})
        observable_include.append(len(circuit_z.measurements)-1)
    for i,stabilizer in enumerate(stabilizers_x):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)})
    for i,stabilizer in enumerate(stabilizers_z):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)+len(stabilizers_x)})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):
        for i in range(majorana_number):
            circuit_z.append({"name":"FDEPOLARIZE1","target":i,"index":i,"p":p_noise})
        for i,stabilizer in enumerate(stabilizers_x):
            circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy),'p':p_measure})
        for i,stabilizer in enumerate(stabilizers_z):
            circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)+len(stabilizers_x),'p':p_measure})
        for i in range(stabilizer_number):
            circuit_z.append({"name":"DETECTOR","target":[-i - 1, -i - stabilizer_number-1]})

    ##  最后一轮测量假设是没有噪声的
    for i,stabilizer in enumerate(stabilizers_x):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)})
    for i,stabilizer in enumerate(stabilizers_z):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)+len(stabilizers_x)})

    ##  测量逻辑算符
    for i,logical_operator in enumerate(logical_occupy):
        circuit_z.append({"name":"MPP","target":logical_operator,"index":i})
        circuit_z.append({"name":"OBSERVABLE_INCLUDE","target":[len(circuit_z.measurements) - 1, observable_include[i]]})

    ##  ===返回线路===
    return circuit_z


#%%  KEY：===将Majorana CSS code转换为线路级噪声下的测试线路===
def MajoranaCSSCode2CircuitLevelCircuit(code,p_noise,p_measure,cycle_number:int):

    ##  ===数据预处理===
    assert isinstance(code,MajoranaCSSCode)
    stabilizers_x=code.generators_x
    stabilizers_z=code.generators_z
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z

    ##  获取logical operators
    logical_occupy=[]
    for i in range(len(logical_x)):
        logical_occupy.append(1j*logical_x[i]@logical_z[i])

    majorana_number=code.physical_number
    stabilizer_number = len(stabilizers_x) + len(stabilizers_z)
    pauli_number=stabilizer_number
    majorana_state_stabilizers=stabilizers_x.tolist()+stabilizers_z.tolist()
    majorana_state_one=logical_occupy+majorana_state_stabilizers
    pauli_state_zero = []
    for i in range(stabilizer_number+len(logical_occupy)):
        pauli_state_zero.append(PauliOperator([],[],1))
    pauli_state_ancilla=[]
    for i in range(pauli_number):
        pauli_state_ancilla.append(PauliOperator([],[i],1))
    pauli_state=pauli_state_zero+pauli_state_ancilla

    majorana_state_zero = []
    for i in range(len(pauli_state_ancilla)):
        majorana_state_zero.append(MajoranaOperator([], [], 1))
    majorana_state_zero = majorana_state_zero
    majorana_state=majorana_state_one+majorana_state_zero

    ##  ---生成线路---
    ##  强制初始化
    circuit_z = Circuit()
    circuit_z.append({"name":"FORCE",
                      "majorana_state":majorana_state,
                      'pauli_state':pauli_state,
                      'pauli_number':pauli_number,
                      'majorana_number':majorana_number})

    ##  第一轮测量假设完美的初始化
    observable_include= []  # 记录可观测量的索引
    for i,logical_operator in enumerate(logical_occupy):
        circuit_z.append({"name":"MPP","target":logical_operator})
        observable_include.append(len(circuit_z.measurements)-1)
    for i,stabilizer in enumerate(stabilizers_x):
        circuit_z.append({"name":"MPP","target":stabilizer})
    for i,stabilizer in enumerate(stabilizers_z):
        circuit_z.append({"name":"MPP","target":stabilizer})

    for i in range(majorana_number):
        circuit_z.append({"name": "FDEPOLARIZE1", "target": i, "p": p_noise})

    for i in range(pauli_number):
        circuit_z.append({"name": "DEPOLARIZE1", "target": i, "p": p_noise})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):
        for i,stabilizer in enumerate(stabilizers_x):
            sequence_temp=syndrome_majorana_measurement_circuit(stabilizer,i,'x',p_noise,p_measure)
            for temp in sequence_temp:
                circuit_z.append(temp)
        for i,stabilizer in enumerate(stabilizers_z):
            sequence_temp=syndrome_majorana_measurement_circuit(stabilizer,i,'z',p_noise,p_measure)
            for temp in sequence_temp:
                circuit_z.append(temp)

        for i in range(stabilizer_number):
            circuit_z.append({"name":"DETECTOR","target":[-i - 1, -i - stabilizer_number-1]})

    ##  最后一轮测量假设是没有噪声的
    for i,stabilizer in enumerate(stabilizers_x):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)})
    for i,stabilizer in enumerate(stabilizers_z):
        circuit_z.append({"name":"MPP","target":stabilizer,"index":i+len(logical_occupy)+len(stabilizers_x)})
    for i in range(stabilizer_number):
        circuit_z.append({"name": "DETECTOR", "target": [-i - 1, -i - stabilizer_number - 1]})

    ##  测量逻辑算符
    for i,logical_operator in enumerate(logical_occupy):
        circuit_z.append({"name":"MPP","target":logical_operator,"index":i})
        circuit_z.append({"name":"OBSERVABLE_INCLUDE","target":[len(circuit_z.measurements) - 1, observable_include[i]]})

    ##  ---返回线路---
    return circuit_z


#%%  KEY：将Pauli CSS code转换为现象级噪声下的测试线路
def PauliCSSCode2PhenomenologicalCircuit(code,p_noise,p_measure,cycle_number:int):
    pass


#%%  KEY：将Pauli CSS code转换为电路级噪声下的测试线路
def PauliCSSCode2CircuitLevelCircuit(code,p_noise,p_measure,cycle_number:int):
    pass


#%%  KEY：将Majorana CSS code转换为码能力下的测试线路
def MajoranaCSSCode2CodeCapacityCircuit(code,p_noise,p_measure,cycle_number:int):
    pass


#%%  KEY：将Pauli CSS code转换为码能力下的测试线路
def PauliCSSCode2CodeCapacityCircuit(code,p_noise,p_measure,cycle_number:int):
    pass


# %%  KEY：===生成Majorana CSS stabilizer测量线路===
def syndrome_majorana_measurement_circuit(stabilizer, qubit_index, type, *args):
    ##  处理输入参数
    if len(args) == 1:
        p_noise = args[0]
        p_measure = args[0] / 10
    elif len(args) == 0:
        p_noise = 0
        p_measure = 0
    elif len(args) == 2:
        p_noise = args[0]
        p_measure = args[1]
    else:
        raise ValueError

    ##  初始化
    sequence = []  # 线路序列
    flag = True  # 门类型标志

    ##  将qubit置于负号匹配
    sequence.append({'name': 'X', 'target': qubit_index})
    sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': p_noise})

    ##  生成syndrome extraction circuit的前一半
    for j in range(len(stabilizer.occupy_x)):
        majorana_index_now = stabilizer.occupy_x[j]

        ##  最后一位与qubit作用CNX gate
        if j == len(stabilizer.occupy_x) - 1:
            sequence.append({'name': 'CNX', 'target': [majorana_index_now, qubit_index], })
            sequence.append({'name': 'FDEPOLARIZE1', 'target': majorana_index_now, 'p': p_noise})
            sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': p_noise})
            break

        ##  其他位与fermionic site作用CNN gate或braid gate
        majorana_index_down = stabilizer.occupy_x[j + 1]  # 后一个fermionic site
        if type == 'X' or type == 'x':
            order_target = [majorana_index_down, majorana_index_now]
        elif type == 'Z' or type == 'z':
            order_target = [majorana_index_now, majorana_index_down]
        else:
            raise ValueError

        ##  作用braid gate
        if flag:
            sequence.append({"name": "B", "target": order_target, })
            sequence.append({'name': 'FDEPOLARIZE1', 'target': order_target, 'p': p_noise})
            flag = False

        ##  作用CNN gate
        else:
            sequence.append({'name': 'CNN', 'target': [majorana_index_now, majorana_index_down], })
            sequence.append({'name': 'FDEPOLARIZE1', 'target': [majorana_index_now, majorana_index_down], 'p': p_noise})
            flag = True

    ##  生成syndrome extraction circuit的另一半
    flag = True
    for j in range(len(stabilizer.occupy_x) - 1):
        majorana_index_now = stabilizer.occupy_x[-1 - j]  # 当前的fermionic site
        majorana_index_up = stabilizer.occupy_x[-1 - j - 1]  # 上一个fermionic site
        if type == 'X' or type == 'x':
            order_target = [majorana_index_now, majorana_index_up]
        elif type == 'Z' or type == 'z':
            order_target = [majorana_index_up, majorana_index_now]
        else:
            raise ValueError

        ##  作用braid gate
        if flag:
            sequence.append({'name': 'N', 'target': [majorana_index_now]})
            sequence.append({'name': 'FDEPOLARIZE1', 'target': majorana_index_now, 'p': p_noise})
            sequence.append({'name': 'braid', 'target': order_target})
            sequence.append({'name': 'FDEPOLARIZE1', 'target': order_target, 'p': p_noise})
            sequence.append({'name': 'N', 'target': [majorana_index_now]})
            sequence.append({'name': 'FDEPOLARIZE1', 'target': majorana_index_now, 'p': p_noise})
            flag = False

        ##  作用CNN gate
        else:
            sequence.append({'name': 'CNN', 'target': [majorana_index_now, majorana_index_up]})
            sequence.append({'name': 'FDEPOLARIZE1', 'target': [majorana_index_now, majorana_index_up], 'p': p_noise})
            flag = True

    ##  在qubit上测量结果并重置
    sequence.append({'name': 'MZ', 'target': qubit_index, 'p': p_measure})
    sequence.append({'name': 'R', 'target': qubit_index})
    sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': p_noise})
    return sequence
