"""
ByggSjekk / nops.no – PDF-rapportgenerator for eiendomsoppslag.

Genererer et strukturert PDF-dokument med:
- Eiendomsidentifikasjon og nøkkeltall
- Verdiestimator
- Bygningsinformasjon
- Byggesakshistorikk (sammendrag)
- Planstatus
- AI-risikovurdering (hvis tilgjengelig)

Bruker fpdf2 (ren Python, ingen systemavhengigheter).
"""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from fpdf import FPDF, XPos, YPos


class EiendomsrapportPDF(FPDF):
    """PDF-rapport for ByggSjekk eiendomsoppslag."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self._setup_fonts()

    def _setup_fonts(self):
        """Sett opp standard fonter."""
        # fpdf2 bruker helvetica som standard (dekker norske tegn ok)
        pass

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(37, 99, 235)  # blue-600
        self.cell(0, 8, "nops.no  |  ByggSjekk Eiendomsrapport", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(226, 232, 240)  # slate-200
        self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)  # slate-500
        self.cell(0, 5, f"Generert av nops.no  |  {date.today().strftime('%d.%m.%Y')}  |  Side {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    # ── Section heading ────────────────────────────────────────────────────────

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(239, 246, 255)  # blue-50
        self.set_text_color(30, 64, 175)  # blue-800
        self.cell(0, 8, f"  {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    # ── Key-value pairs ───────────────────────────────────────────────────────

    def kv_row(self, key: str, value: str, bold_value: bool = False):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(55, 6, key + ":", new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.set_text_color(15, 23, 42)
        if bold_value:
            self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)

    # ── Disclaimer box ────────────────────────────────────────────────────────

    def disclaimer_box(self, text: str):
        self.ln(4)
        self.set_fill_color(254, 252, 232)  # yellow-50
        self.set_draw_color(234, 179, 8)  # yellow-500
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(133, 77, 14)  # yellow-800
        self.multi_cell(0, 5, text, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)


def _fmt_kr(v: float | None) -> str:
    if v is None:
        return "–"
    return f"{v:,.0f} kr".replace(",", " ")


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "–"
    return f"+{v:.1f}%"


def generer_eiendomsrapport(eiendomsdata: dict[str, Any]) -> bytes:
    """
    Genererer en PDF-rapport for et eiendomsoppslag.

    Args:
        eiendomsdata: Dict fra /property/full endepunktet

    Returns:
        PDF-innhold som bytes
    """
    pdf = EiendomsrapportPDF()

    knr = eiendomsdata.get("kommunenummer", "")
    gnr = eiendomsdata.get("gnr", "")
    bnr = eiendomsdata.get("bnr", "")
    eiendom = eiendomsdata.get("eiendom") or {}
    bygninger = eiendomsdata.get("bygninger") or []
    byggesaker = eiendomsdata.get("byggesaker") or []
    kommune = eiendomsdata.get("kommune") or {}
    verdi = eiendomsdata.get("verdiestimator") or {}
    planrapport = eiendomsdata.get("planrapport") or {}
    ai = eiendomsdata.get("ai_analyse") or {}

    # ── Tittel ────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    adresse = eiendom.get("adresse") or f"Gnr. {gnr} Bnr. {bnr}"
    pdf.cell(0, 10, adresse, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    postnr = eiendom.get("postnummer", "")
    poststed = eiendom.get("poststed", "")
    kommunenavn = kommune.get("kommunenavn", knr)
    pdf.cell(0, 6, f"{postnr} {poststed}  ·  {kommunenavn}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # ── Nøkkeltall ─────────────────────────────────────────────────────────────
    pdf.section_title("Eiendomsidentifikasjon")
    pdf.kv_row("Kommunenummer", knr)
    pdf.kv_row("Gårdsnummer / Bruksnummer", f"{gnr} / {bnr}")
    if eiendom.get("areal_m2"):
        pdf.kv_row("Tomteareal", f"{eiendom['areal_m2']:.0f} m²")
    if eiendom.get("eierform"):
        pdf.kv_row("Eierform", eiendom["eierform"])
    if eiendom.get("matrikkel_id"):
        pdf.kv_row("Matrikkel-ID", str(eiendom["matrikkel_id"]))

    # ── Verdiestimator ────────────────────────────────────────────────────────
    if verdi and verdi.get("estimert_verdi"):
        pdf.section_title("Verdiestimator")
        pdf.kv_row("Estimert markedsverdi", _fmt_kr(verdi.get("estimert_verdi")), bold_value=True)
        ki = verdi.get("konfidensintervall")
        if ki and len(ki) == 2:
            pdf.kv_row("Konfidensintervall (±25%)", f"{_fmt_kr(ki[0])} – {_fmt_kr(ki[1])}")
        if verdi.get("pris_per_kvm"):
            pdf.kv_row("Pris per m²", f"{verdi['pris_per_kvm']:,.0f} kr/m²")
        if verdi.get("kommune_median_pris"):
            pdf.kv_row("Kommunemedian", _fmt_kr(verdi.get("kommune_median_pris")))
        if verdi.get("kommune_prisvekst_prosent"):
            pdf.kv_row("Prisvekst (5 år)", _fmt_pct(verdi.get("kommune_prisvekst_prosent")))
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        metode = verdi.get("estimat_metode", "")
        if metode:
            pdf.cell(0, 5, f"Metode: {metode}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # ── Bygninger ─────────────────────────────────────────────────────────────
    if bygninger:
        pdf.section_title(f"Bygninger ({len(bygninger)})")
        for i, b in enumerate(bygninger):
            if i > 0:
                pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            btype = b.get("bygningstype") or "Ukjent type"
            pdf.cell(0, 6, f"  {btype}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            if b.get("byggeaar"):
                pdf.kv_row("  Byggeår", str(b["byggeaar"]))
            if b.get("bruksareal"):
                pdf.kv_row("  Bruksareal", f"{b['bruksareal']:.0f} m²")
            if b.get("bygningstatus"):
                pdf.kv_row("  Status", b["bygningstatus"])

    # ── Byggesaker ────────────────────────────────────────────────────────────
    if byggesaker:
        pdf.section_title(f"Byggesaker ({len(byggesaker)})")
        for sak in byggesaker[:10]:  # maks 10 for plass
            tittel = sak.get("tittel") or sak.get("beskrivelse") or sak.get("sakstype") or "Ukjent sak"
            status = sak.get("status") or ""
            dato = sak.get("vedtaksdato") or sak.get("innsendtdato") or ""
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            # Truncate long titles
            tittel_trunc = (tittel[:70] + "...") if len(tittel) > 73 else tittel
            pdf.cell(0, 5, f"  • {tittel_trunc}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 116, 139)
            meta = "    " + "  |  ".join(filter(None, [status, dato[:10] if dato else ""]))
            if meta.strip():
                pdf.cell(0, 4, meta, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if len(byggesaker) > 10:
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 5, f"  ... og {len(byggesaker) - 10} til", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # ── Arealplaner ───────────────────────────────────────────────────────────
    gjeldende_planer = planrapport.get("gjeldende_planer") or []
    if gjeldende_planer:
        pdf.section_title(f"Gjeldende arealplaner ({len(gjeldende_planer)})")
        for plan in gjeldende_planer[:5]:
            pdf.set_font("Helvetica", "", 9)
            navn = plan.get("plan_navn") or "Ukjent plan"
            navn_trunc = (navn[:70] + "...") if len(navn) > 73 else navn
            pdf.cell(0, 5, f"  • {navn_trunc}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 116, 139)
            status = plan.get("status") or ""
            dato = plan.get("vedtaksdato") or ""
            meta = "    " + "  |  ".join(filter(None, [status, dato[:10] if dato else ""]))
            if meta.strip():
                pdf.cell(0, 4, meta, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)

    dispensasjoner = planrapport.get("dispensasjoner") or []
    if dispensasjoner:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(161, 98, 7)  # amber
        pdf.cell(0, 5, f"  Dispensasjoner: {len(dispensasjoner)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # ── AI-analyse ────────────────────────────────────────────────────────────
    if ai and ai.get("sammendrag"):
        pdf.section_title("AI-risikovurdering")
        nivaa = ai.get("risiko_nivaa", "")
        score = ai.get("risiko_score")
        if nivaa:
            score_str = f"  (score: {score*100:.0f}%)" if score is not None else ""
            pdf.set_font("Helvetica", "B", 10)
            farger = {"LAV": (22, 163, 74), "MIDDELS": (161, 98, 7), "HØY": (220, 38, 38), "KRITISK": (153, 27, 27)}
            rgb = farger.get(nivaa, (0, 0, 0))
            pdf.set_text_color(*rgb)
            pdf.cell(0, 6, f"  Risikonivå: {nivaa}{score_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)

        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, ai.get("sammendrag", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        finninger = ai.get("nøkkelfinninger") or []
        if finninger:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "  Nøkkelfinninger:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for f in finninger[:5]:
                f_trunc = (f[:80] + "...") if len(f) > 83 else f
                pdf.cell(0, 5, f"  • {f_trunc}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if ai.get("fraskrivelse"):
            pdf.disclaimer_box(ai["fraskrivelse"])

    # ── Generell fraskrivelse ─────────────────────────────────────────────────
    pdf.disclaimer_box(
        "MERK: Denne rapporten er generert automatisk fra offentlig tilgjengelige datakilder. "
        "Informasjonen er kun ment som beslutningsstøtte og erstatter ikke faglig vurdering "
        "fra arkitekt, takstmann eller juridisk rådgiver. nops.no tar ikke ansvar for eventuelle "
        "feil eller mangler i rapporten."
    )

    return pdf.output()
