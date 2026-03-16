"""
Abstracted LLM adapter supporting OpenAI and Anthropic (Claude).

Usage:
    adapter = get_llm_adapter()
    result = await adapter.classify_document(filename, content_preview)

Set LLM_PROVIDER=openai or LLM_PROVIDER=anthropic in environment.
"""
from __future__ import annotations

import abc
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentClassificationResult:
    document_type: str
    confidence: float
    method: str = "llm"
    reasoning: str = ""


@dataclass
class DeviationExplanationResult:
    explanation: str
    suggested_action: str
    legal_context: str


class LLMAdapter(abc.ABC):
    """Abstract LLM adapter interface."""

    @abc.abstractmethod
    async def classify_document(
        self,
        filename: str,
        content_preview: str,
    ) -> DocumentClassificationResult:
        """
        Classify a document based on filename and content preview.

        Returns document_type from: floor_plan, situasjonsplan, godkjent_tegning,
        fasadetegning, snittegning, rammetillatelse, igangsettingstillatelse,
        ferdigattest, brukstillatelse, other
        """

    @abc.abstractmethod
    async def extract_plan_metadata(
        self,
        text_content: str,
    ) -> dict:
        """Extract structured metadata from plan document text."""

    @abc.abstractmethod
    async def explain_deviation(
        self,
        category: str,
        description: str,
        context: dict,
    ) -> DeviationExplanationResult:
        """
        Generate a Norwegian explanation for a detected deviation.

        IMPORTANT: Must NOT use words like 'ulovlig', 'godkjent' or 'krever søknad'
        as categorical conclusions. Frame as observations only.
        """


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT-4o implementation."""

    DOCUMENT_TYPES = [
        "floor_plan", "situasjonsplan", "godkjent_tegning", "fasadetegning",
        "snittegning", "rammetillatelse", "igangsettingstillatelse",
        "ferdigattest", "brukstillatelse", "other",
    ]

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def classify_document(self, filename: str, content_preview: str) -> DocumentClassificationResult:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            prompt = f"""Du er en ekspert på norske byggedokumenter.
Klassifiser dette dokumentet basert på filnavn og innholdsforhåndsvisning.

Filnavn: {filename}
Innhold (forhåndsvisning): {content_preview[:1000]}

Svar KUN med ett av disse dokumenttypene (ingen annen tekst):
{', '.join(self.DOCUMENT_TYPES)}

Deretter på neste linje, skriv confidence (0.0-1.0).
Deretter på neste linje, en kort norsk forklaring (1 setning)."""

            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0,
            )
            lines = response.choices[0].message.content.strip().split("\n")
            document_type = lines[0].strip() if lines else "other"
            if document_type not in self.DOCUMENT_TYPES:
                document_type = "other"
            confidence = float(lines[1].strip()) if len(lines) > 1 else 0.7
            reasoning = lines[2].strip() if len(lines) > 2 else ""
            return DocumentClassificationResult(
                document_type=document_type,
                confidence=min(max(confidence, 0.0), 1.0),
                method="openai",
                reasoning=reasoning,
            )
        except Exception as exc:
            logger.error("OpenAI classification failed: %s", exc)
            return DocumentClassificationResult(document_type="other", confidence=0.1, method="openai_error")

    async def extract_plan_metadata(self, text_content: str) -> dict:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            prompt = f"""Ekstraher strukturert metadata fra denne norske byggetegningen.
Svar med JSON-objekt med feltene: total_area_m2, floor_count, room_count, address, year_built (eller null).

Dokument: {text_content[:3000]}"""
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0,
                response_format={"type": "json_object"},
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.error("OpenAI metadata extraction failed: %s", exc)
            return {}

    async def explain_deviation(self, category: str, description: str, context: dict) -> DeviationExplanationResult:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            prompt = f"""Du er arkitekt-assistent i Norge. Forklar følgende observasjon på norsk.
VIKTIG: Bruk ALDRI ordene "ulovlig", "godkjent" eller "krever søknad" som en kategorisk konklusjon.
Skriv som en faglig observasjon, ikke som en juridisk vurdering.

Kategori: {category}
Beskrivelse: {description}
Kontekst: {context}

Svar med JSON: {{"explanation": "...", "suggested_action": "...", "legal_context": "..."}}"""
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            import json
            data = json.loads(response.choices[0].message.content)
            return DeviationExplanationResult(
                explanation=data.get("explanation", ""),
                suggested_action=data.get("suggested_action", ""),
                legal_context=data.get("legal_context", ""),
            )
        except Exception as exc:
            logger.error("OpenAI deviation explanation failed: %s", exc)
            return DeviationExplanationResult(
                explanation=description,
                suggested_action="Se avviket nærmere etter.",
                legal_context="",
            )


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude implementation."""

    DOCUMENT_TYPES = OpenAIAdapter.DOCUMENT_TYPES

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.api_key = api_key
        self.model = model

    async def classify_document(self, filename: str, content_preview: str) -> DocumentClassificationResult:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = f"""Du er en ekspert på norske byggedokumenter.
Klassifiser dette dokumentet basert på filnavn og innholdsforhåndsvisning.

Filnavn: {filename}
Innhold (forhåndsvisning): {content_preview[:1000]}

Svar KUN med ett av disse dokumenttypene:
{', '.join(self.DOCUMENT_TYPES)}

Deretter confidence (0.0-1.0) på neste linje.
Deretter en norsk forklaring (1 setning) på neste linje."""

            message = await client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            lines = message.content[0].text.strip().split("\n")
            document_type = lines[0].strip() if lines else "other"
            if document_type not in self.DOCUMENT_TYPES:
                document_type = "other"
            confidence = float(lines[1].strip()) if len(lines) > 1 else 0.7
            reasoning = lines[2].strip() if len(lines) > 2 else ""
            return DocumentClassificationResult(
                document_type=document_type,
                confidence=min(max(confidence, 0.0), 1.0),
                method="anthropic",
                reasoning=reasoning,
            )
        except Exception as exc:
            logger.error("Anthropic classification failed: %s", exc)
            return DocumentClassificationResult(document_type="other", confidence=0.1, method="anthropic_error")

    async def extract_plan_metadata(self, text_content: str) -> dict:
        try:
            import anthropic
            import json
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = f"""Ekstraher strukturert metadata fra denne norske byggetegningen.
Svar KUN med et JSON-objekt med feltene: total_area_m2, floor_count, room_count, address, year_built.

Dokument: {text_content[:3000]}"""
            message = await client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(message.content[0].text)
        except Exception as exc:
            logger.error("Anthropic metadata extraction failed: %s", exc)
            return {}

    async def explain_deviation(self, category: str, description: str, context: dict) -> DeviationExplanationResult:
        try:
            import anthropic
            import json
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            prompt = f"""Du er arkitekt-assistent i Norge. Forklar observasjonen på norsk.
VIKTIG: Bruk ALDRI "ulovlig", "godkjent" eller "krever søknad" som kategorisk konklusjon.

Kategori: {category}
Beskrivelse: {description}
Kontekst: {context}

Svar BARE med JSON: {{"explanation": "...", "suggested_action": "...", "legal_context": "..."}}"""
            message = await client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            data = json.loads(message.content[0].text)
            return DeviationExplanationResult(
                explanation=data.get("explanation", ""),
                suggested_action=data.get("suggested_action", ""),
                legal_context=data.get("legal_context", ""),
            )
        except Exception as exc:
            logger.error("Anthropic deviation explanation failed: %s", exc)
            return DeviationExplanationResult(
                explanation=description,
                suggested_action="Se avviket nærmere etter.",
                legal_context="",
            )


class NoOpAdapter(LLMAdapter):
    """Fallback adapter when no LLM provider is configured."""

    async def classify_document(self, filename: str, content_preview: str) -> DocumentClassificationResult:
        return DocumentClassificationResult(document_type="other", confidence=0.1, method="noop")

    async def extract_plan_metadata(self, text_content: str) -> dict:
        return {}

    async def explain_deviation(self, category: str, description: str, context: dict) -> DeviationExplanationResult:
        return DeviationExplanationResult(
            explanation=description,
            suggested_action="Arkitekt bør vurdere avviket.",
            legal_context="",
        )


_adapter_instance: LLMAdapter | None = None


def get_llm_adapter() -> LLMAdapter:
    """Factory: returns the configured LLM adapter (singleton)."""
    global _adapter_instance
    if _adapter_instance is not None:
        return _adapter_instance

    from app.core.config import settings
    provider = getattr(settings, "LLM_PROVIDER", "noop").lower()

    if provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if api_key:
            _adapter_instance = OpenAIAdapter(api_key=api_key)
        else:
            logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY not set. Using NoOpAdapter.")
            _adapter_instance = NoOpAdapter()
    elif provider == "anthropic":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or ""
        if api_key:
            _adapter_instance = AnthropicAdapter(api_key=api_key)
        else:
            logger.warning("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set. Using NoOpAdapter.")
            _adapter_instance = NoOpAdapter()
    else:
        _adapter_instance = NoOpAdapter()

    return _adapter_instance
