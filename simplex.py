from fractions import Fraction


def _guardar_tabla(tabla, nombres, base, fase, iteraciones):
    paso = {
        "numero": len(iteraciones),
        "fase": fase,
        "columnas": nombres + ["LD"],
        "base": [nombres[j] for j in base],
        "tabla": [[str(valor) for valor in fila] for fila in tabla],
        "pivote": None,
    }
    iteraciones.append(paso)
    return paso


def _poner_objetivo(tabla, base, costos):
    """Construye el renglón objetivo y anula los costos de la base."""
    renglon = [-costo for costo in costos] + [Fraction(0)]

    for fila, columna in enumerate(base):
        costo_basico = costos[columna]
        if costo_basico:
            renglon = [
                valor + costo_basico * valor_fila
                for valor, valor_fila in zip(renglon, tabla[fila])
            ]

    tabla[-1] = renglon


def _pivotear(tabla, base, nombres, fila, columna, paso, cocientes):
    pivote = tabla[fila][columna]
    paso["pivote"] = {
        "fila": fila,
        "columna": columna,
        "valor": str(pivote),
        "entra": nombres[columna],
        "sale": nombres[base[fila]],
        "cocientes": [
            str(cocientes[i]) if i in cocientes else None
            for i in range(len(base))
        ],
    }

    tabla[fila] = [valor / pivote for valor in tabla[fila]]

    for i, renglon in enumerate(tabla):
        if i != fila and renglon[columna]:
            multiplicador = renglon[columna]
            tabla[i] = [
                valor - multiplicador * valor_pivote
                for valor, valor_pivote in zip(renglon, tabla[fila])
            ]

    base[fila] = columna


def _optimizar(tabla, base, nombres, fase, iteraciones):
    bases_visitadas = set()
    usar_bland = False

    while True:
        paso = _guardar_tabla(tabla, nombres, base, fase, iteraciones)
        candidatas = [
            j for j in range(len(nombres)) if tabla[-1][j] < 0
        ]

        if not candidatas:
            return None

        # Si una base se repite, la regla de Bland evita que el método cicle.
        base_actual = tuple(sorted(base))
        if base_actual in bases_visitadas:
            usar_bland = True
        bases_visitadas.add(base_actual)

        columna = candidatas[0] if usar_bland else min(
            candidatas, key=lambda j: tabla[-1][j]
        )

        cocientes = {
            i: tabla[i][-1] / tabla[i][columna]
            for i in range(len(base))
            if tabla[i][columna] > 0
        }

        if not cocientes:
            return nombres[columna]

        fila = min(cocientes, key=lambda i: (cocientes[i], base[i]))
        _pivotear(tabla, base, nombres, fila, columna, paso, cocientes)


def simplex_primal(objetivo, restricciones, sentido="max"):
    """Resuelve un problema lineal con variables de decisión no negativas."""
    if sentido not in {"max", "min"}:
        raise ValueError("El sentido debe ser 'max' o 'min'.")
    if not objetivo or not restricciones:
        raise ValueError("Captura al menos una variable y una restricción.")

    n = len(objetivo)
    costos_originales = [Fraction(str(valor)) for valor in objetivo]
    nombres = [f"x{i + 1}" for i in range(n)]
    base = []
    artificiales = set()
    filas = []
    signos_inversos = {"<=": ">=", ">=": "<=", "=": "="}

    for i, (coeficientes, signo, lado_derecho) in enumerate(
        restricciones, start=1
    ):
        if len(coeficientes) != n or signo not in signos_inversos:
            raise ValueError(f"Revisa los coeficientes y el signo de R{i}.")

        fila = [Fraction(str(valor)) for valor in coeficientes]
        rhs = Fraction(str(lado_derecho))

        if rhs < 0:
            fila = [-valor for valor in fila]
            rhs = -rhs
            signo = signos_inversos[signo]

        extras = {}
        if signo in {"<=", ">="}:
            columna = len(nombres)
            nombres.append(f"h{i}" if signo == "<=" else f"e{i}")
            extras[columna] = Fraction(1 if signo == "<=" else -1)

        if signo != "<=":
            columna = len(nombres)
            nombres.append(f"a{i}")
            artificiales.add(columna)
            extras[columna] = Fraction(1)

        base.append(columna)
        filas.append((fila, extras, rhs))

    tabla = [
        fila + [
            extras.get(j, Fraction(0)) for j in range(n, len(nombres))
        ] + [rhs]
        for fila, extras, rhs in filas
    ]
    tabla.append([Fraction(0)] * (len(nombres) + 1))
    iteraciones = []

    if artificiales:
        costos_auxiliares = [
            Fraction(-1 if j in artificiales else 0)
            for j in range(len(nombres))
        ]
        _poner_objetivo(tabla, base, costos_auxiliares)
        if _optimizar(tabla, base, nombres, "Fase I", iteraciones) is not None:
            raise ArithmeticError("El objetivo auxiliar debe estar acotado.")

        if tabla[-1][-1] < 0:
            return {
                "estado": "infactible",
                "mensaje": "Las restricciones no tienen una solución factible común.",
                "columnas": nombres + ["LD"],
                "iteraciones": iteraciones,
            }

        # Una artificial básica puede quedar en cero al terminar la Fase I.
        i = 0
        while i < len(base):
            if base[i] not in artificiales:
                i += 1
                continue

            reemplazo = next(
                (
                    j for j in range(len(nombres))
                    if j not in artificiales and tabla[i][j] != 0
                ),
                None,
            )

            if reemplazo is None:
                # Al quitar las artificiales, esta fila se reduce a 0 = 0.
                del tabla[i]
                del base[i]
            else:
                paso = _guardar_tabla(
                    tabla, nombres, base, "Retiro de artificiales", iteraciones
                )
                _pivotear(tabla, base, nombres, i, reemplazo, paso, {})
                i += 1

        conservar = [j for j in range(len(nombres)) if j not in artificiales]
        nueva_posicion = {j: k for k, j in enumerate(conservar)}
        tabla = [[fila[j] for j in conservar] + [fila[-1]] for fila in tabla]
        base = [nueva_posicion[j] for j in base]
        nombres = [nombres[j] for j in conservar]

    factor = 1 if sentido == "max" else -1
    costos = [factor * valor for valor in costos_originales]
    costos += [Fraction(0)] * (len(nombres) - n)
    _poner_objetivo(tabla, base, costos)
    variable_no_acotada = _optimizar(tabla, base, nombres, "Fase II", iteraciones)

    resultado = {"columnas": nombres + ["LD"], "iteraciones": iteraciones}

    if variable_no_acotada is not None:
        return {
            **resultado,
            "estado": "no_acotado",
            "mensaje": f"{variable_no_acotada} puede mejorar el objetivo sin límite.",
        }

    base_final = {nombres[j]: str(tabla[i][-1]) for i, j in enumerate(base)}
    return {
        **resultado,
        "estado": "optimo",
        "variables": {nombre: base_final.get(nombre, "0") for nombre in nombres[:n]},
        "base_final": base_final,
        "valor_objetivo": str(factor * tabla[-1][-1]),
    }


if __name__ == "__main__":
    resultado = simplex_primal(
        objetivo=[3, 2],
        restricciones=[
            ([1, 1], ">=", 2),
            ([1, 1], "<=", 4),
            ([1, 0], "<=", 2),
        ],
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

    if resultado["estado"] == "optimo":
        print("\nVariables:", resultado["variables"])
        print("Valor óptimo de Z:", resultado["valor_objetivo"])
    else:
        print("\n", resultado["mensaje"])