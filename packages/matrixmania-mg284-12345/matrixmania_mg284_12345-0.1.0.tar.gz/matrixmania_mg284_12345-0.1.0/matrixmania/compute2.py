# Matrixmultiplikation, Transponieren einer Matrix und Rotation

from typing import List
import math
from tabulate import tabulate



# Matrixmultiplikation

def matmul(a: List[List[int | float]], b: List[List[int | float]]) -> List[List[int | float]]:

    """
    Multiply 2 matrices
    :param a: matrix 1
    :type a: List[List[int | float]]
    :param b: matrix 2
    :type b: List[List[int | float]]
    :return: Product of the 2 matrices
    :rtype: List[List[int | float]]
    :raises ValueError: when width of matrix 1 is not equal to height of matrix 2
    """

    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])

    if not cols_a == rows_b:
        raise ValueError("Width of first matrix is not equal to height of second matrix!")

    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]

    return result




#Transponieren einer Matrix

def transpose(f: List[List[int | float]]) -> List[List[int | float]]:

    """
    Transpose the matrix
    :param f: the given matrix
    :type f: List[List[int | float]]
    :return: transposed matrix
    :rtype: List[List[int | float]]
    :raises ValueError: when matrix is empty or not all rows have the same amount of columns
    """

    if f is None:
        raise ValueError("Matrix is empty!")

    rows_f, cols_f = len(f), len(f[0])

    for i in range(rows_f):
        if not len(f[i]) == cols_f:
            raise ValueError("Not all rows have the same amount of columns!")

    result = [[0 for _ in range(rows_f)] for _ in range(cols_f)]
    for i in range(rows_f):
        for j in range(cols_f):
            result[j][i] = f[i][j]

    return result




# Rotation

def rot_2D(degree: int | float) -> List[List[int | float]]:

    """
    Rotationmatrix of given angle
    :param degree: the given angle
    :type degree: int | float
    :return: rotationmatrix
    :rtype: List[List[int | float]]
    """

    angle : int | float = math.radians(degree)
    matrix_rotation = [[math.cos(angle), -math.sin(angle)],
                       [math.sin(angle), math.cos(angle)]
                      ]

    return matrix_rotation




if __name__ == "__main__":

    # hab ich alles selbst programmiert
    
    # matrixmultiplikation

    matrix_a = [[3, 4, -1, 4],
                [-2, 2, 5, 1]
                ]
    matrix_b = [[1, 3, -2],
                [2, 5, 1],
                [-1, 4, -4],
                [2, 3, 6]
                ]
    matrix_d = [[1, 2],
                [3, 4]
                ]

    print("Matrix A:")
    print(tabulate(matrix_a))

    try:
        matrix_c : List[List[int | float]] = matmul(matrix_a, matrix_b)
        print("Ergebnis C = A * B:")
        print("[")
        for row in matrix_c:
            print(row)
        print("]")
    except ValueError as v:
        print(f"Mistake for matrix_c: {v}")

    try:
        matrix_e : List[List[int | float]] = matmul(matrix_a, matrix_d)
        print("Ergebnis E = A * D:")
        for row in matrix_e:
            print(row)
    except ValueError as v:
        print(f"Mistake for matrix_e: {v}")



    # transponieren

    matrix_f = [[1, 2, 3],
                [4, 5, 6]
                ]

    matrix_g : List[List[int | float]] = transpose(matrix_f)
    print("[")
    for row in matrix_g:
        print(row)
    print("]")


    # rotation matrix

    matrix_r : List[List[int | float]] = rot_2D(90)
    print("[")
    for row in matrix_r:
        print(row)
    print("]")