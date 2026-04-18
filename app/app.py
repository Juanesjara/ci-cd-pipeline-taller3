"""
Aplicación principal Flask para la calculadora.
Maneja rutas y operaciones básicas (suma, resta, etc.).
"""

# app/app.py
import os
from flask import Flask, render_template, request
from .calculadora import sumar, restar, multiplicar, dividir, potencia, modulo

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-insecure-key")


@app.route("/", methods=["GET"])
def index():
    """Muestra la página principal."""
    return render_template("index.html", resultado=None)


@app.route("/", methods=["POST"])
def calcular():
    """Procesa el formulario y realiza la operación seleccionada."""
    resultado = None
    if request.method == "POST":
        try:
            num1 = float(request.form["num1"])
            num2 = float(request.form["num2"])
            operacion = request.form["operacion"]

            if operacion == "sumar":
                resultado = sumar(num1, num2)
            elif operacion == "restar":
                resultado = restar(num1, num2)
            elif operacion == "multiplicar":
                resultado = multiplicar(num1, num2)
            elif operacion == "dividir":
                resultado = dividir(num1, num2)
            elif operacion == "potencia":
                resultado = potencia(num1, num2)
            elif operacion == "modulo":
                resultado = modulo(num1, num2)
            else:
                resultado = "Operación no válida"
        except ValueError:
            resultado = "Error: Introduce números válidos"
        except ZeroDivisionError:
            resultado = "Error: No se puede dividir por cero"

    return render_template("index.html", resultado=resultado)


@app.route("/health" methods=["GET"])
def health():
    """Health check endpoint para el ALB."""
    return "OK", 200


if __name__ == "__main__":  # pragma: no cover
    app_port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, port=app_port, host="0.0.0.0")
