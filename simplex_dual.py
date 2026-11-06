from fractions import Fraction

from simplex import _guardar_tabla, _pivotear


def simplex_dual(objetivo, restricciones, sentido="max"):
    """Aplica Simplex Dual desde una base de holguras dualmente factible."""
    if sentido not in {"max", "min"}:
        raise ValueError("El sentido debe ser 'max' o 'min'.")
    if not objetivo or not restricciones:
        raise ValueError("Captura al menos una variable y una restricción.")

    n = len(objetivo)
    factor = 1 if sentido == "max" else -1
    costos = [factor * Fraction(str(valor)) for valor in objetivo]
    filas = []

    for i, (coeficientes, signo, lado_derecho) in enumerate(
        restricciones, start=1
    ):
        if len(coeficientes) != n or signo not in {"<=", ">=", "="}:
            raise ValueError(f"Revisa los coeficientes y el signo de R{i}.")

        fila = [Fraction(str(valor)) for valor in coeficientes]
        rhs = Fraction(str(lado_derecho))

        if signo in {"<=", "="}:
            filas.append((fila, rhs))
        if signo in {">=", "="}:
            filas.append(([-valor for valor in fila], -rhs))

    # Todas las filas tienen forma <=, así que agregamos una holgura por fila.
    m = len(filas)
    nombres = [f"x{i + 1}" for i in range(n)]
    nombres += [f"h{i + 1}" for i in range(m)]
    base = list(range(n, n + m))

    tabla = [
        fila + [Fraction(int(i == j)) for j in range(m)] + [rhs]
        for i, (fila, rhs) in enumerate(filas)
    ]
    tabla.append([-costo for costo in costos] + [Fraction(0)] * (m + 1))

    iteraciones = []
    resultado = {"columnas": nombres + ["LD"], "iteraciones": iteraciones}
    bases_visitadas = set()

    while True:
        paso = _guardar_tabla(
            tabla, nombres, base, "Simplex Dual", iteraciones
        )

        if any(valor < 0 for valor in tabla[-1][:-1]):
            return {
                **resultado,
                "estado": "base_dual_no_disponible",
                "mensaje": (
                    "La base inicial de holguras no cumple la condición "
                    "del Simplex Dual. Puedes resolver este caso con Simplex Primal."
                ),
            }

        fila = min(range(m), key=lambda i: tabla[i][-1])

        if tabla[fila][-1] >= 0:
            base_final = {
                nombres[j]: str(tabla[i][-1]) for i, j in enumerate(base)
            }
            return {
                **resultado,
                "estado": "optimo",
                "variables": {
                    nombre: base_final.get(nombre, "0") for nombre in nombres[:n]
                },
                "base_final": base_final,
                "valor_objetivo": str(factor * tabla[-1][-1]),
            }

        base_actual = tuple(sorted(base))
        if base_actual in bases_visitadas:
            return {
                **resultado,
                "estado": "ciclo",
                "mensaje": (
                    "Se repitió una base durante el pivoteo dual. "
                    "Puedes resolver este caso con Simplex Primal."
                ),
            }
        bases_visitadas.add(base_actual)

        cocientes = {
            j: tabla[-1][j] / (-tabla[fila][j])
            for j in range(len(nombres))
            if tabla[fila][j] < 0
        }

        if not cocientes:
            return {
                **resultado,
                "estado": "infactible",
                "mensaje": (
                    f"La fila de {nombres[base[fila]]} tiene lado derecho "
                    "negativo y ninguna columna puede corregirlo."
                ),
            }

        columna = min(cocientes, key=lambda j: (cocientes[j], j))
        _pivotear(tabla, base, nombres, fila, columna, paso, {})
        paso["pivote"]["cocientes_duales"] = [
            str(cocientes[j]) if j in cocientes else None
            for j in range(len(nombres))
        ]


if __name__ == "__main__":
    resultado = simplex_dual(
        objetivo=[2, 3],
        restricciones=[([1, 1], ">=", 4)],
        sentido="min",
    )

    for paso in resultado["iteraciones"]:
        print(f"\nTabla {paso['numero']} | {paso['fase']}")
        print("Base:", ", ".join(paso["base"]))
        print("\t".join(paso["columnas"]))
        for fila in paso["tabla"]:
            print("\t".join(fila))

        if paso["pivote"]:
            pivote = paso["pivote"]
            print(f"Entra {pivote['entra']} y sale {pivote['sale']}")
            print("Cocientes por columna:", pivote["cocientes_duales"])

    if resultado["estado"] == "optimo":
        print("\nVariables:", resultado["variables"])
        print("Valor óptimo de Z:", resultado["valor_objetivo"])
    else:
        print("\n" + resultado["mensaje"])