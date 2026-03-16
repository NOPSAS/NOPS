"""
ByggSjekk – API v1 router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, cases, deviations, documents, municipality, plans, reviews, rules,
    address_search, billing,
)

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)
api_router.include_router(
    cases.router,
    prefix="/cases",
    tags=["Cases"],
)
api_router.include_router(
    documents.router,
    prefix="/cases/{case_id}/documents",
    tags=["Documents"],
)
api_router.include_router(
    deviations.router,
    prefix="/cases/{case_id}/deviations",
    tags=["Deviations"],
)
api_router.include_router(
    reviews.router,
    prefix="/cases/{case_id}",
    tags=["Reviews & Reports"],
)
api_router.include_router(rules.router, prefix="", tags=["Rules"])
api_router.include_router(
    plans.router,
    prefix="/cases/{case_id}/plans",
    tags=["Plans"],
)
api_router.include_router(
    municipality.router,
    prefix="/cases/{case_id}/municipality-requests",
    tags=["Municipality"],
)
api_router.include_router(
    address_search.router,
    prefix="/search",
    tags=["Address Search"],
)
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])

# ---------------------------------------------------------------------------
# Property lookup endpoint (municipality connector integration)
# Placeholder – will be provided by the property/municipality agent.
# ---------------------------------------------------------------------------
try:
    from app.api.v1.endpoints import property as property_endpoints  # noqa: F401

    api_router.include_router(
        property_endpoints.router,
        prefix="/property",
        tags=["Property"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import visualisering as visualisering_endpoints  # noqa: F401

    api_router.include_router(
        visualisering_endpoints.router,
        prefix="/visualisering",
        tags=["Visualisering"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import investering as investering_endpoints  # noqa: F401

    api_router.include_router(
        investering_endpoints.router,
        prefix="/investering",
        tags=["Investering"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import utbygging as utbygging_endpoints  # noqa: F401

    api_router.include_router(
        utbygging_endpoints.router,
        prefix="/utbygging",
        tags=["Utbygging"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import nyheter as nyheter_endpoints  # noqa: F401

    api_router.include_router(
        nyheter_endpoints.router,
        prefix="/nyheter",
        tags=["Nyheter"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import tomter as tomter_endpoints  # noqa: F401

    api_router.include_router(
        tomter_endpoints.router,
        prefix="/tomter",
        tags=["Tomter"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import finn as finn_endpoints  # noqa: F401

    api_router.include_router(
        finn_endpoints.router,
        prefix="/finn",
        tags=["Finn.no"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import dokumentanalyse as dok_endpoints  # noqa: F401

    api_router.include_router(
        dok_endpoints.router,
        prefix="/dokumentanalyse",
        tags=["Dokumentanalyse"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import juridisk as juridisk_endpoints  # noqa: F401

    api_router.include_router(
        juridisk_endpoints.router,
        prefix="/juridisk",
        tags=["Juridisk"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import dispensasjon as dispensasjon_endpoints  # noqa: F401

    api_router.include_router(
        dispensasjon_endpoints.router,
        prefix="/dispensasjon",
        tags=["Dispensasjon"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import naboklage as naboklage_endpoints  # noqa: F401

    api_router.include_router(
        naboklage_endpoints.router,
        prefix="/naboklage",
        tags=["Naboklage"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import tomtedeling as tomtedeling_endpoints  # noqa: F401

    api_router.include_router(
        tomtedeling_endpoints.router,
        prefix="/tomtedeling",
        tags=["Tomtedeling"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import tilbygg as tilbygg_endpoints  # noqa: F401

    api_router.include_router(
        tilbygg_endpoints.router,
        prefix="/tilbygg",
        tags=["Tilbygg"],
    )
except ImportError:
    pass

try:
    from app.api.v1.endpoints import bestemmelser as bestemmelser_endpoints  # noqa: F401

    api_router.include_router(
        bestemmelser_endpoints.router,
        prefix="/bestemmelser",
        tags=["Bestemmelser"],
    )
except ImportError:
    pass
