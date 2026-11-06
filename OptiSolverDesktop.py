from pathlib import Path

import webview

from simplex import simplex_primal
from simplex_dual import simplex_dual


class OptiSolverAPI:
    def resolver(self, problema):
        metodos = {
            "primal": simplex_primal,
            "dual": simplex_dual,
        }

        try:
            resolver_metodo = metodos[problema["metodo"]]
            return resolver_metodo(
                objetivo=problema["objetivo"],
                restricciones=problema["restricciones"],
                sentido=problema["sentido"],
            )
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            return {
                "estado": "error_entrada",
                "mensaje": f"Revisa los datos del problema. Detalle: {error}",
            }


def main():
    pagina = Path(__file__).resolve().with_name("index.html")

    if not pagina.is_file():
        raise FileNotFoundError(f"No se encontró el formulario en {pagina}")

    webview.create_window(
        title="OptiSolver Desktop",
        url=str(pagina),
        js_api=OptiSolverAPI(),
        width=1100,
        height=800,
    )
    webview.start(http_server=True)


if __name__ == "__main__":
    main()