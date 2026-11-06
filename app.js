"use strict";

const formulario = document.getElementById("formulario-problema");
const cantidadVariables = document.getElementById("num-variables");
const cantidadRestricciones = document.getElementById("num-restricciones");
const coeficientesObjetivo = document.getElementById("coeficientes-objetivo");
const matrizRestricciones = document.getElementById("matriz-restricciones");
const botonResolver = document.getElementById("resolver");
const estado = document.getElementById("estado");
const resultados = document.getElementById("resultados");
const resumen = document.getElementById("resumen");
const iteraciones = document.getElementById("iteraciones");

const limite = 20;

cantidadVariables.max = limite;
cantidadRestricciones.max = limite;

function mostrarEstado(texto, tipo = "") {
    if (tipo) {
        estado.dataset.tipo = tipo;
    } else {
        delete estado.dataset.tipo;
    }

    estado.textContent = texto;
}

function crearCampoNumerico(id, etiqueta, valor) {
    const campo = document.createElement("input");
    campo.id = id;
    campo.name = id;
    campo.type = "number";
    campo.step = "any";
    campo.required = true;
    campo.value = valor ?? "0";
    campo.setAttribute("aria-label", etiqueta);
    return campo;
}

function crearSelectorSigno(fila, valor) {
    const selector = document.createElement("select");
    selector.id = `signo-${fila}`;
    selector.name = selector.id;
    selector.setAttribute("aria-label", `Signo de la restricción ${fila}`);

    selector.add(new Option("≤", "<="));
    selector.add(new Option("≥", ">="));
    selector.add(new Option("=", "="));
    selector.value = valor ?? "<=";

    return selector;
}

function agregarEncabezado(fila, texto, alcance) {
    const encabezado = document.createElement("th");
    encabezado.textContent = texto;
    encabezado.scope = alcance;
    fila.append(encabezado);
}

function generarFormulario() {
    if (!cantidadVariables.validity.valid || !cantidadRestricciones.validity.valid) {
        mostrarEstado(
            `Escribe un número entero del 1 al ${limite} en cada cantidad.`,
            "error_entrada"
        );
        return;
    }

    const variables = cantidadVariables.valueAsNumber;
    const restricciones = cantidadRestricciones.valueAsNumber;

    const camposAnteriores = document.querySelectorAll(
        "#coeficientes-objetivo input, #matriz-restricciones input, #matriz-restricciones select"
    );
    const valoresAnteriores = new Map(
        [...camposAnteriores].map(campo => [campo.id, campo.value])
    );

    const nuevosCoeficientes = document.createDocumentFragment();

    for (let columna = 1; columna <= variables; columna++) {
        const id = `objetivo-${columna}`;
        const grupo = document.createElement("div");
        const etiqueta = document.createElement("label");

        etiqueta.htmlFor = id;
        etiqueta.textContent = `x${columna}`;

        grupo.append(
            etiqueta,
            crearCampoNumerico(
                id,
                `Coeficiente de x${columna} en la función objetivo`,
                valoresAnteriores.get(id)
            )
        );

        nuevosCoeficientes.append(grupo);
    }

    const tabla = document.createElement("table");
    tabla.setAttribute("aria-label", "Coeficientes de las restricciones");

    const encabezado = tabla.createTHead().insertRow();
    agregarEncabezado(encabezado, "Restricción", "col");

    for (let columna = 1; columna <= variables; columna++) {
        agregarEncabezado(encabezado, `x${columna}`, "col");
    }

    agregarEncabezado(encabezado, "Signo", "col");
    agregarEncabezado(encabezado, "Lado derecho", "col");

    const cuerpo = tabla.createTBody();

    for (let fila = 1; fila <= restricciones; fila++) {
        const renglon = cuerpo.insertRow();
        agregarEncabezado(renglon, `R${fila}`, "row");

        for (let columna = 1; columna <= variables; columna++) {
            const id = `restriccion-${fila}-${columna}`;

            renglon.insertCell().append(
                crearCampoNumerico(
                    id,
                    `Coeficiente de x${columna} en la restricción ${fila}`,
                    valoresAnteriores.get(id)
                )
            );
        }

        renglon.insertCell().append(
            crearSelectorSigno(fila, valoresAnteriores.get(`signo-${fila}`))
        );

        const id = `lado-derecho-${fila}`;

        renglon.insertCell().append(
            crearCampoNumerico(
                id,
                `Lado derecho de la restricción ${fila}`,
                valoresAnteriores.get(id)
            )
        );
    }

    coeficientesObjetivo.replaceChildren(nuevosCoeficientes);
    matrizRestricciones.replaceChildren(tabla);
    mostrarEstado(
        `Matriz generada con ${variables} variables y ${restricciones} restricciones.`
    );
}

function leerProblema() {
    const n = cantidadVariables.valueAsNumber;
    const m = cantidadRestricciones.valueAsNumber;

    // Enviamos los números como texto para que Python use fracciones exactas.
    const valor = id => document.getElementById(id).value;

    return {
        metodo: valor("metodo"),
        sentido: valor("objetivo"),
        objetivo: Array.from({ length: n }, (_, j) => valor(`objetivo-${j + 1}`)),
        restricciones: Array.from({ length: m }, (_, i) => {
            const fila = i + 1;
            const coeficientes = Array.from(
                { length: n },
                (_, j) => valor(`restriccion-${fila}-${j + 1}`)
            );

            return [
                coeficientes,
                valor(`signo-${fila}`),
                valor(`lado-derecho-${fila}`)
            ];
        })
    };
}

function agregarParrafo(contenedor, texto) {
    const parrafo = document.createElement("p");
    parrafo.textContent = texto;
    contenedor.append(parrafo);
}

function mostrarAsignaciones(etiqueta, asignaciones) {
    const valores = Object.entries(asignaciones)
        .map(([nombre, valor]) => `${nombre} = ${valor}`)
        .join(", ");

    agregarParrafo(resumen, `${etiqueta}: ${valores || "Vacía"}`);
}

function mostrarIteraciones(pasos, sentido) {
    let indice = 0;

    const navegacion = document.createElement("div");
    const anterior = document.createElement("button");
    const siguiente = document.createElement("button");
    const posicion = document.createElement("span");
    const contenido = document.createElement("div");

    navegacion.className = "navegacion-iteraciones";
    anterior.type = "button";
    anterior.textContent = "Anterior";
    siguiente.type = "button";
    siguiente.textContent = "Siguiente";
    posicion.setAttribute("aria-live", "polite");

    navegacion.append(anterior, posicion, siguiente);
    iteraciones.append(navegacion, contenido);

    function mostrarPaso() {
        const paso = pasos[indice];
        const pivote = paso.pivote;
        const tabla = document.createElement("table");
        const titulo = document.createElement("caption");

        titulo.textContent = `Tabla ${paso.numero} · ${paso.fase}`;
        tabla.append(titulo);
        contenido.replaceChildren(tabla);

        const encabezado = tabla.createTHead().insertRow();
        agregarEncabezado(encabezado, "Base", "col");

        for (const columna of paso.columnas) {
            agregarEncabezado(encabezado, columna, "col");
        }

        const cuerpo = tabla.createTBody();
        const esFaseAuxiliar =
            paso.fase === "Fase I" || paso.fase === "Retiro de artificiales";
        const objetivoInterno = esFaseAuxiliar
            ? "−Suma de artificiales"
            : sentido === "min" ? "−Z" : "Z";

        paso.tabla.forEach((valores, i) => {
            const renglon = cuerpo.insertRow();
            agregarEncabezado(renglon, paso.base[i] ?? objetivoInterno, "row");

            valores.forEach((valor, j) => {
                const celda = renglon.insertCell();
                celda.textContent = valor;

                if (pivote && i === pivote.fila && j === pivote.columna) {
                    celda.classList.add("celda-pivote");
                }
            });
        });

        if (pivote) {
            agregarParrafo(
                contenido,
                `Entra ${pivote.entra}, sale ${pivote.sale}. Pivote = ${pivote.valor}.`
            );

            const esDual = Boolean(pivote.cocientes_duales);
            const cocientes = esDual ? pivote.cocientes_duales : pivote.cocientes;
            const candidatos = cocientes.flatMap((valor, i) => {
                const nombre = esDual ? paso.columnas[i] : paso.base[i];
                return valor === null ? [] : [`${nombre} = ${valor}`];
            });

            if (candidatos.length > 0) {
                agregarParrafo(contenido, `Cocientes: ${candidatos.join(", ")}`);
            }
        }

        posicion.textContent = `${indice + 1} de ${pasos.length}`;
        anterior.disabled = indice === 0;
        siguiente.disabled = indice === pasos.length - 1;
    }

    anterior.addEventListener("click", () => {
        indice--;
        mostrarPaso();
    });

    siguiente.addEventListener("click", () => {
        indice++;
        mostrarPaso();
    });

    mostrarPaso();
}

function habilitarResolucion() {
    botonResolver.disabled = false;
}

window.addEventListener("pywebviewready", habilitarResolucion);

if (window.pywebview?.api?.resolver) {
    habilitarResolucion();
}

cantidadVariables.addEventListener("change", generarFormulario);
cantidadRestricciones.addEventListener("change", generarFormulario);

formulario.addEventListener("submit", async evento => {
    evento.preventDefault();

    if (botonResolver.disabled) {
        return;
    }

    // Sincroniza la matriz si se envía el formulario con Enter.
    generarFormulario();

    if (!formulario.reportValidity()) {
        return;
    }

    const problema = leerProblema();

    botonResolver.disabled = true;
    resultados.hidden = true;
    resumen.replaceChildren();
    iteraciones.replaceChildren();
    mostrarEstado("Resolviendo…");

    try {
        const respuesta = await window.pywebview.api.resolver(problema);
        const pasos = respuesta.iteraciones ?? [];

        if (respuesta.estado === "optimo") {
            mostrarEstado("Solución óptima encontrada.", "optimo");
            agregarParrafo(resumen, `Valor óptimo de Z = ${respuesta.valor_objetivo}`);
            mostrarAsignaciones("Vector óptimo", respuesta.variables);
            mostrarAsignaciones("Variables básicas finales", respuesta.base_final);
        } else {
            const titulos = {
                infactible: "Problema infactible",
                no_acotado: "Problema no acotado",
                base_dual_no_disponible: "Base inicial no apta para Simplex Dual",
                ciclo: "Se repitió una base",
                error_entrada: "Datos inválidos"
            };

            const titulo = titulos[respuesta.estado] ?? "Error";
            mostrarEstado(`${titulo}. ${respuesta.mensaje}`, respuesta.estado);
        }

        if (pasos.length > 0) {
            mostrarIteraciones(pasos, problema.sentido);
        }

        resultados.hidden = respuesta.estado !== "optimo" && pasos.length === 0;
        estado.scrollIntoView({ block: "start" });
    } catch (error) {
        mostrarEstado(
            `No se pudo completar el cálculo. ${error.message ?? error}`,
            "error_entrada"
        );
        estado.scrollIntoView({ block: "nearest" });
    } finally {
        botonResolver.disabled = false;
    }
});

generarFormulario();