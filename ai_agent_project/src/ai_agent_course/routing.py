from __future__ import annotations

import os
import re
from typing import Literal, Sequence

from pydantic import BaseModel, Field


RouteName = Literal[
    "search_course",
    "calculator",
    "external_lookup",
    "direct_answer",
]


class RouteDecision(BaseModel):
    """Contrato validado para la decisión del router.

    ``route`` limita las salidas posibles; ``confidence`` y ``reason`` agregan
    información útil para inspección. El objeto describe una decisión, no ejecuta
    la capacidad elegida.
    """

    route: RouteName
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=3, max_length=180)



def build_router_prompt(
    user_message: str,
    capabilities: Sequence[dict],
) -> str:
    """Construye el prompt de clasificación a partir de capacidades declaradas.

    Args:
        user_message: Consulta que queremos enrutar.
        capabilities: Contratos con nombre y descripción de cada capacidad.

    Returns:
        Prompt textual que pide seleccionar exactamente una ruta sin ejecutarla.
    """
    lines = [
        "Clasificá la consulta en exactamente una capacidad.",
        "No ejecutes ninguna capacidad.",
        "",
        "CAPACIDADES:",
    ]

    # Las descripciones son parte del contrato semántico: explican al router
    # cuándo corresponde elegir cada capacidad.
    for capability in capabilities:
        lines.append(
            f"- {capability['name']}: {capability['description']}"
        )

    lines.extend([
        "",
        f"CONSULTA: {user_message}",
    ])

    return "\n".join(lines)


class RuleSemanticRouter:
    """Fallback determinístico para estudiar routing sin depender de un LLM.

    Reproduce el mismo contrato ``route(message, capabilities)`` para que el
    benchmark sea ejecutable offline. Sus reglas son didácticas, no generales.
    """

    name = "rule-router-smoke-only"

    def route(
        self,
        user_message: str,
        capabilities: Sequence[dict],
    ) -> RouteDecision:
        """Clasifica una consulta mediante reglas y devuelve una decisión.

        Args:
            user_message: Mensaje que se quiere enrutar.
            capabilities: Se recibe para mantener el mismo contrato que el router LLM.

        Returns:
            ``RouteDecision``. No invoca ninguna capacidad.
        """
        text = user_message.lower().strip()

        # El orden importa: primero detectamos necesidades que no debe resolver
        # el corpus (cálculo exacto o información vigente), y recién después KB.
        explicit_math = re.search(
            r"\d+(?:[\.,]\d+)?\s*[\+\-\*/]\s*\d+(?:[\.,]\d+)?",
            text,
        )
        calculation_markers = {
            "calculá",
            "calcula",
            "cuánto da",
            "cuanto da",
            "cuántas quedan",
            "cuantas quedan",
            "diferencia",
            "sumá",
            "suma",
            "multiplicá",
            "multiplica",
        }

        if explicit_math or (
            any(marker in text for marker in calculation_markers)
            and re.search(r"\d", text)
        ):
            return RouteDecision(
                route="calculator",
                confidence=0.96,
                reason="La consulta requiere una operación matemática exacta.",
            )

        current_markers = {
            "hoy",
            "actual",
            "ahora",
            "cotización",
            "tipo de cambio",
            "clima",
            "estado del servicio",
        }

        if any(marker in text for marker in current_markers):
            return RouteDecision(
                route="external_lookup",
                confidence=0.92,
                reason="La respuesta depende de información externa o vigente.",
            )

        corpus_markers = {
            "curso",
            "clase",
            "mrr",
            "rrf",
            "bm25",
            "vacaciones",
            "reintegro",
            "credencial",
            "contraseña",
            "política",
            "capacitación",
            "trabajo remoto",
            "factura",
            "portal",
            "integración",
            "api",
            "sso",
            "perfil",
        }

        if any(marker in text for marker in corpus_markers):
            return RouteDecision(
                route="search_course",
                confidence=0.90,
                reason="La respuesta depende del corpus interno disponible.",
            )

        return RouteDecision(
            route="direct_answer",
            confidence=0.70,
            reason="No se detecta necesidad de cálculo, corpus ni dato externo.",
        )


class GeminiSemanticRouter:
    """Router opcional que usa Structured Output de Gemini para clasificar.

    Mantiene el mismo contrato que el fallback por reglas, lo que permite cambiar
    implementación sin modificar el benchmark ni el código consumidor.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-lite",
    ):
        """Inicializa el cliente de Gemini.

        Args:
            api_key: Credencial del proveedor.
            model: Modelo que realizará la clasificación.

        Returns:
            None. Configura cliente, modelo y nombre del router.
        """
        if not api_key:
            raise ValueError("API key vacía")

        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.name = model

    def route(
        self,
        user_message: str,
        capabilities: Sequence[dict],
    ) -> RouteDecision:
        """Pide al modelo una decisión estructurada de routing.

        Args:
            user_message: Consulta a clasificar.
            capabilities: Capacidades disponibles y sus descripciones.

        Returns:
            ``RouteDecision`` validada por Pydantic.

        El modelo solo selecciona una capacidad; la ejecución queda fuera de C8.
        """
        from google.genai import types

        prompt = build_router_prompt(
            user_message,
            capabilities,
        )

        # response_schema obliga a que la salida respete el mismo contrato
        # estructurado que usamos en el fallback determinístico.
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=RouteDecision,
            ),
        )

        # Preferimos la respuesta ya parseada por el SDK. Si no está disponible,
        # validamos manualmente el JSON textual con el mismo modelo Pydantic.
        if getattr(response, "parsed", None) is not None:
            return response.parsed

        return RouteDecision.model_validate_json(
            response.text or "{}"
        )
