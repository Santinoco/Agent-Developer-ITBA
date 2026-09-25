from pathlib import Path
import tempfile
import unittest

from practicas_python_esencial import (
    Conversacion,
    contar_por_rol,
    filtrar_modelos_baratos,
    resumen_conversacion,
)


class PracticasPythonEsencialTests(unittest.TestCase):
    def test_resumen_conversacion(self) -> None:
        resumen = resumen_conversacion([
            {"role": "user", "tokens": 12},
            {"role": "assistant", "tokens": 95},
        ])
        self.assertEqual(resumen["total_tokens"], 107)
        self.assertEqual(resumen["promedio_tokens"], 53.5)
        self.assertAlmostEqual(resumen["costo_total"], 0.00001605)

    def test_filtrar_modelos_baratos(self) -> None:
        catalogo = {
            "barato": {"precio": 0.15, "contexto": 128_000},
            "caro": {"precio": 3.0, "contexto": 128_000},
            "poco_contexto": {"precio": 0.0, "contexto": 8_000},
        }
        self.assertEqual(set(filtrar_modelos_baratos(catalogo)), {"barato"})

    def test_conteo_por_rol(self) -> None:
        mensajes = [{"role": "user"}, {"role": "user"}, {"role": "assistant"}]
        self.assertEqual(contar_por_rol(mensajes), {"user": 2, "assistant": 1})

    def test_conversacion_exporta_json(self) -> None:
        conversacion = Conversacion()
        conversacion.agregar("user", "Hola mundo")
        with tempfile.TemporaryDirectory() as directorio:
            destino = Path(directorio) / "conversacion.json"
            conversacion.exportar(destino)
            self.assertTrue(destino.exists())
            self.assertEqual(conversacion.conteo_por_rol(), {"user": 1})


if __name__ == "__main__":
    unittest.main()
