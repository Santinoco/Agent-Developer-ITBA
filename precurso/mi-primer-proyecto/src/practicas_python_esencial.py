"""Soluciones guiadas para las prácticas de Python esencial.

Ejecutar desde la carpeta ``mi-primer-proyecto``:
    env/Scripts/python.exe src/practicas_python_esencial.py
"""

from dataclasses import dataclass, field
from pathlib import Path
import json


def resumen_conversacion(mensajes: list[dict[str, str | int]]) -> dict[str, float]:
    """Calcula tokens totales, costo y promedio de una conversación."""
    precio_por_millon = 0.15
    total_tokens = sum(int(mensaje["tokens"]) for mensaje in mensajes)
    costo_total = total_tokens / 1_000_000 * precio_por_millon
    promedio_tokens = total_tokens / len(mensajes) if mensajes else 0.0

    return {
        "total_tokens": total_tokens,
        "costo_total": costo_total,
        "promedio_tokens": promedio_tokens,
    }


def filtrar_modelos_baratos(
    catalogo: dict[str, dict[str, float | int]],
    precio_maximo: float = 0.5,
    contexto_minimo: int = 100_000,
) -> dict[str, dict[str, float | int]]:
    """Devuelve modelos cuyo precio y contexto cumplen los límites indicados."""
    return {
        nombre: datos
        for nombre, datos in catalogo.items()
        if float(datos["precio"]) < precio_maximo
        and int(datos["contexto"]) > contexto_minimo
    }


def contar_por_rol(mensajes: list[dict[str, str | int]]) -> dict[str, int]:
    """Cuenta cuántos mensajes hay para cada rol."""
    conteo: dict[str, int] = {}
    for mensaje in mensajes:
        rol = str(mensaje["role"])
        conteo[rol] = conteo.get(rol, 0) + 1
    return conteo


@dataclass
class Mensaje:
    rol: str
    contenido: str

    @property
    def tokens_estimados(self) -> int:
        """Estima tokens a partir de las palabras del contenido."""
        return max(1, int(len(self.contenido.split()) / 0.75))


@dataclass
class Conversacion:
    mensajes: list[Mensaje] = field(default_factory=list)
    modelo: str = "gemini-2.5-flash"
    precio_por_millon: float = 0.0

    def agregar(self, rol: str, contenido: str) -> None:
        self.mensajes.append(Mensaje(rol=rol, contenido=contenido))

    def conteo_por_rol(self) -> dict[str, int]:
        return contar_por_rol(
            [{"role": mensaje.rol, "content": mensaje.contenido} for mensaje in self.mensajes]
        )

    def total_tokens(self) -> int:
        return sum(mensaje.tokens_estimados for mensaje in self.mensajes)

    def costo_estimado(self) -> float:
        return self.total_tokens() / 1_000_000 * self.precio_por_millon

    def mensaje_mas_largo(self) -> Mensaje | None:
        if not self.mensajes:
            return None
        return max(self.mensajes, key=lambda mensaje: mensaje.tokens_estimados)

    def exportar(self, ruta: Path) -> None:
        datos = [
            {"rol": mensaje.rol, "contenido": mensaje.contenido}
            for mensaje in self.mensajes
        ]
        ruta.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def ejecutar_practicas() -> None:
    mensajes = [
        {"role": "user", "content": "¿Qué es RAG?", "tokens": 12},
        {"role": "assistant", "content": "RAG es...", "tokens": 95},
        {"role": "user", "content": "Dame un ejemplo.", "tokens": 8},
        {"role": "assistant", "content": "Por ejemplo...", "tokens": 120},
    ]
    resumen = resumen_conversacion(mensajes)
    print("=== Práctica 1 ===")
    print(f"Tokens totales: {resumen['total_tokens']}")
    print(f"Costo total: ${resumen['costo_total']:.8f}")
    print(f"Promedio por mensaje: {resumen['promedio_tokens']:.2f}")

    catalogo = {
        "gpt-4o": {"precio": 3.0, "contexto": 128_000},
        "gpt-4o-mini": {"precio": 0.15, "contexto": 128_000},
        "gemini-2.5-flash": {"precio": 0.0, "contexto": 1_000_000},
        "claude-3-5-sonnet": {"precio": 3.0, "contexto": 200_000},
        "claude-haiku": {"precio": 0.25, "contexto": 200_000},
    }
    baratos = filtrar_modelos_baratos(catalogo)
    print("\n=== Práctica 2 ===")
    print("Modelos baratos:", ", ".join(baratos))

    print("\n=== Práctica 3 ===")
    print("Mensajes por rol:", contar_por_rol(mensajes))

    conversacion = Conversacion(precio_por_millon=0.15)
    conversacion.agregar("system", "Eres un experto en inteligencia artificial.")
    conversacion.agregar("user", "¿Qué es RAG y por qué es importante en producción?")
    conversacion.agregar(
        "assistant",
        "RAG combina la generación de un modelo con información recuperada de documentos.",
    )
    conversacion.agregar("user", "¿Cuáles son sus limitaciones?")

    salida = Path(__file__).parent.parent / "conversacion_demo.json"
    conversacion.exportar(salida)
    mensaje_largo = conversacion.mensaje_mas_largo()
    print("\n=== Proyecto integrador ===")
    print(f"Mensajes: {len(conversacion.mensajes)}")
    print(f"Por rol: {conversacion.conteo_por_rol()}")
    print(f"Tokens estimados: {conversacion.total_tokens()}")
    print(f"Costo estimado: ${conversacion.costo_estimado():.8f}")
    if mensaje_largo:
        print(f"Mensaje más largo: [{mensaje_largo.rol}] {mensaje_largo.tokens_estimados} tokens")
    print(f"Exportado en: {salida.name}")


if __name__ == "__main__":
    ejecutar_practicas()
