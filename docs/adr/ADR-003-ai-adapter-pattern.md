# ADR-003: Abstrakt AI-adapter for LLM-integrasjon

**Status:** Akseptert
**Dato:** 2024
**Beslutningstakere:** Konsepthus AS

---

## Kontekst

ByggSjekk bruker store språkmodeller (LLM) med visjon-kapabiliteter for to kjerneoppgaver:
1. **Plan-parsing:** Ekstrahere romdata (rom, areal, funksjon) fra plantegnings-bilder
2. **Avviksdetektor:** Sammenligne to strukturerte planer og identifisere avvik

Det finnes flere aktuelle LLM-leverandører med ulike styrker, priser og tilgjengelighet:
- **OpenAI GPT-4o** – sterk visjonsforståelse, god API-stabilitet
- **Anthropic Claude** – sterk resonnering, lang kontekst, god norsk-forståelse
- **Azure OpenAI** – foretrukket ved GDPR/databehandlingsavtale-krav fra offentlig sektor
- **Open-source modeller** (Llama, Mistral via Ollama) – for å unngå leverandørlås

Uten abstraksjon ville all AI-kode bli tett koblet til én leverandørs SDK. Leverandørbytte eller A/B-testing ville krevd betydelig refaktorering.

---

## Beslutning

Vi implementerer et **abstrakt adapter-mønster** (strategimønster) for alle LLM-integrasjoner.

```python
class LLMAdapterInterface(ABC):
    """Abstrakt grensesnitt for LLM-leverandører."""

    @abstractmethod
    async def analyze_plan_image(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Analyser et plantegningsbilde og returner strukturert respons."""
        ...

    @abstractmethod
    async def extract_room_data(
        self,
        image_bytes: bytes,
    ) -> list[RoomData]:
        """Ekstraher romdata fra plantegningsbilde."""
        ...

    @abstractmethod
    async def compare_plans(
        self,
        approved_plan: StructuredPlan,
        current_plan: StructuredPlan,
    ) -> DeviationAnalysis:
        """Sammenlign to strukturerte planer og identifiser avvik."""
        ...
```

Implementasjoner:
- `OpenAIAdapter` – bruker `openai` Python SDK (GPT-4o med vision)
- `AnthropicAdapter` – bruker `anthropic` Python SDK (Claude med vision)
- `AzureOpenAIAdapter` – Azure-hosted OpenAI for GDPR-krav
- `MockLLMAdapter` – deterministiske svar for enhetstesting

---

## Begrunnelse

### Strategimønsteret gir:

1. **Leverandøruavhengighet:** Vi kan bytte fra GPT-4o til Claude (eller omvendt) ved å endre én miljøvariabel (`LLM_PROVIDER`). Ingen endringer i domenekoden.

2. **A/B-testing:** Vi kan sende samme tegning til to leverandører og sammenligne resultater. Verdifullt for kvalitetssikring av AI-vurderinger.

3. **Testbarhet:** `MockLLMAdapter` returnerer predefinerte, deterministiske svar. Enhetstetster trenger ikke mock-biblioteker og avhenger ikke av nettverkstilgang.

4. **Kostkontroll:** Vi kan rute enkle oppgaver til billigere modeller (f.eks. gpt-4o-mini for pre-screening) og tyngre oppgaver til GPT-4o eller Claude Opus.

5. **Fremtidssikring:** Åpen kildekode-modeller (Llama 3, Mistral) kan implementeres bak samme grensesnitt. Lokale modeller via Ollama gir mulighet for on-premises deployment for kommuner med strenge databehandlingskrav.

### Respons-wrapper

Alle adaptere returnerer en `LLMResponse`-wrapper som inkluderer:
```python
@dataclass
class LLMResponse:
    content: dict              # Parsert JSON-innhold
    model: str                 # Faktisk modell brukt
    model_version: str         # Versjon/snapshot
    prompt_hash: str           # SHA-256 av input-prompt (sporbarhet)
    raw_response: str          # Rå tekst-respons fra LLM
    input_tokens: int          # Antall input-tokens (kostnadssporing)
    output_tokens: int         # Antall output-tokens
    confidence: float          # Selvrapportert eller beregnet confidence
    latency_ms: int            # Svartid
```

Denne wrapperen lagres i databasen (`raw_llm_response`-kolonnen) for etterprøvbarhet.

### Prompt-håndtering

Prompts er eksternalisert til `apps/api/prompts/`-mappen som `.jinja2`-filer:
```
apps/api/prompts/
├── extract_rooms.j2        # Ekstraher romdata fra plantegning
├── compare_plans.j2        # Sammenlign to planer
└── classify_deviation.j2   # Klassifiser avvik
```

Dette gjør prompt-engineering mulig uten kodeendringer og gir versjonskontroll på prompts.

---

## Alternativer vurdert

### Direkte SDK-kall uten abstraksjon

**Forkastet fordi:**
- Tett kobling til én leverandør
- Testing krever mock-biblioteker eller nettverkstilgang
- Leverandørbytte krever refaktorering av domenekoden

### LangChain / LlamaIndex

**Vurdert, forkastet fordi:**
- LangChain er et komplett rammeverk med egne abstraksjoner som kan konflikte med vår arkitektur
- Mye overhead og avhengigheter vi ikke trenger
- Vår bruk av LLM er avgrenset til spesifikke, godt-definerte oppgaver – ikke generell agent-logikk
- Vi foretrekker å eie abstraksjonslaget selv for full kontroll

### LiteLLM

**Interessant, forkastet foreløpig fordi:**
- LiteLLM er et tynt OpenAI-kompatibelt lag over mange leverandører
- Kan introduseres som implementasjonsdetalj i en adapter (f.eks. `LiteLLMAdapter`)
- Beholder grensesnittet vårt mot domenekoden

---

## Konsekvenser

- **Positiv:** Leverandøruavhengighet og enkel A/B-testing
- **Positiv:** Fullstendig testbar domenekode uten nettverkskall
- **Positiv:** Sporbarhet for alle AI-vurderinger via `LLMResponse`-wrapperen
- **Nøytral:** Krever at alle LLM-kall går gjennom adapteren. Håndheves via code review.
- **Nøytral:** Prompt-ekstraksjon til `.j2`-filer øker kompleksiteten litt, men gir bedre separasjon

---

## Gjennomgangspunkt

- Vurder LiteLLM-integrasjon som implementasjonsdetalj i adapterne ved fase 4
- Vurder lokale modeller via Ollama ved kommunekontrakter med GDPR-krav
