from enum import Enum


class Extension(str, Enum):
    """Enumaration of Strangeworks SDK integrations."""

    CIRQ_IONQ = "cirq-ionq"
    QISKIT_IONQ = "qiskit-ionq"
    IBM_QISKIT_RUNTIME = "ibm-qiskit-runtime"
    AWS_BRAKET = "amazon-braket"
    DWAVE = "dwave"
    RIGETTI = "rigetti"
