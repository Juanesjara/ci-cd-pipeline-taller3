# app/calculadora.py
"""
Módulo de operaciones matemáticas básicas.

Este módulo proporciona funciones para realizar operaciones
aritméticas simples como suma, resta, multiplicación y división.
Incluye validación para evitar divisiones por cero.

Módulo de operaciones matemáticas básicas.
"""

AUTOR = "defrancov, jlmurillob, jejaramilr"


def sumar(a, b):
    """- sumar(a, b): retorna la suma de dos números"""
    return a + b


def restar(a, b):
    """- restar(a, b): retorna la resta de dos números"""
    return a - b


def multiplicar(a, b):
    """- multiplicar(a, b): retorna el producto de dos números"""
    return a * b


def dividir(a, b):
    """- dividir(a, b): retorna la división de dos números"""
    if b == 0:
        raise ZeroDivisionError("No se puede dividir por cero")
    return a / b


def potencia(a, b):
    """- potencia(a, b): retorna a elevado a la b"""
    return a**b


def modulo(a, b):
    """- modulo(a, b): retorna el residuo de la división de a entre b"""
    if b == 0:
        raise ZeroDivisionError("No se puede dividir por cero")
    return a % b
