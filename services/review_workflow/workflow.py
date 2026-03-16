"""
ByggSjekk – Review workflow state machine.

Tilstandsmaskin for arkitektgjennomgang av avviksrapporter.

Tilstander:
  PENDING     → Gjennomgang opprettet, ingen handling utført
  IN_PROGRESS → Arkitekt er aktivt i gang med gjennomgang
  COMPLETED   → Alle avvik er vurdert og gjennomgangen er ferdigstilt
  REJECTED    → Gjennomgangen er avvist (f.eks. utilstrekkelig dokumentasjon)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tilstander
# ---------------------------------------------------------------------------


class ReviewState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class DeviationDecision(str, Enum):
    CONFIRMED = "CONFIRMED"         # Arkitekt bekrefter avviket
    DISMISSED = "DISMISSED"         # Arkitekt avviser avviket (falsk positiv)
    REQUIRES_ACTION = "REQUIRES_ACTION"  # Krever videre oppfølging
    NOTED = "NOTED"                 # Notert, ingen umiddelbar handling


# ---------------------------------------------------------------------------
# Datamodeller
# ---------------------------------------------------------------------------


@dataclass
class DeviationDecisionRecord:
    deviation_id: str
    decision: DeviationDecision
    notes: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    reviewer_id: str = ""


@dataclass
class AuditEntry:
    actor_id: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


@dataclass
class WorkflowSession:
    """Representerer en aktiv gjennomgangsøkt."""
    case_id: str
    review_id: str
    state: ReviewState
    reviewer_id: str
    deviation_decisions: dict[str, DeviationDecisionRecord] = field(default_factory=dict)
    audit_log: list[AuditEntry] = field(default_factory=list)
    summary_notes: str = ""
    started_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    completed_at: str | None = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""


class IncompleteReviewError(Exception):
    """Raised when trying to complete a review with undecided deviations."""


# ---------------------------------------------------------------------------
# Tilstandsmaskin
# ---------------------------------------------------------------------------


class ReviewWorkflowStateMachine:
    """
    Håndterer tilstandstransisjoner for arkitektgjennomgang.

    Gyldige transisjoner:
      PENDING     → IN_PROGRESS  (start_review)
      IN_PROGRESS → COMPLETED    (complete_review – alle avvik må ha beslutning)
      IN_PROGRESS → REJECTED     (reject_review)
      COMPLETED   → IN_PROGRESS  (reopen_review – ved ny informasjon)
    """

    _VALID_TRANSITIONS: dict[ReviewState, set[ReviewState]] = {
        ReviewState.PENDING: {ReviewState.IN_PROGRESS},
        ReviewState.IN_PROGRESS: {ReviewState.COMPLETED, ReviewState.REJECTED},
        ReviewState.COMPLETED: {ReviewState.IN_PROGRESS},
        ReviewState.REJECTED: {ReviewState.IN_PROGRESS},
    }

    def start_review(
        self,
        session: WorkflowSession,
        reviewer_id: str,
    ) -> WorkflowSession:
        """
        Starter gjennomgangen – setter tilstand til IN_PROGRESS.

        Args:
            session:     WorkflowSession fra databasen
            reviewer_id: ID til den gjennomgående arkitekten

        Returns:
            Oppdatert WorkflowSession

        Raises:
            InvalidTransitionError: Hvis gjennomgangen ikke er i PENDING-tilstand
        """
        self._assert_valid_transition(session.state, ReviewState.IN_PROGRESS)
        session.state = ReviewState.IN_PROGRESS
        session.reviewer_id = reviewer_id
        session.audit_log.append(AuditEntry(
            actor_id=reviewer_id,
            action="start_review",
            details={"previous_state": "PENDING"},
        ))
        logger.info("Gjennomgang %s startet av %s", session.review_id, reviewer_id)
        return session

    def record_deviation_decision(
        self,
        session: WorkflowSession,
        deviation_id: str,
        decision: DeviationDecision,
        notes: str = "",
        reviewer_id: str = "",
    ) -> WorkflowSession:
        """
        Registrerer arkitektens beslutning for ett avvik.

        Args:
            session:      WorkflowSession
            deviation_id: ID til avviket
            decision:     Beslutning (CONFIRMED, DISMISSED, osv.)
            notes:        Valgfrie kommentarer fra arkitekt
            reviewer_id:  ID til gjennomfører

        Returns:
            Oppdatert WorkflowSession
        """
        if session.state != ReviewState.IN_PROGRESS:
            raise InvalidTransitionError(
                f"Kan ikke registrere beslutning i tilstand {session.state}. "
                f"Gjennomgangen må være IN_PROGRESS."
            )

        record = DeviationDecisionRecord(
            deviation_id=deviation_id,
            decision=decision,
            notes=notes,
            reviewer_id=reviewer_id or session.reviewer_id,
        )
        session.deviation_decisions[deviation_id] = record
        session.audit_log.append(AuditEntry(
            actor_id=reviewer_id or session.reviewer_id,
            action="deviation_decision",
            details={
                "deviation_id": deviation_id,
                "decision": decision.value,
                "has_notes": bool(notes),
            },
        ))
        logger.debug(
            "Avvik %s: beslutning=%s (case=%s)",
            deviation_id, decision.value, session.case_id,
        )
        return session

    def complete_review(
        self,
        session: WorkflowSession,
        expected_deviation_ids: list[str],
        summary_notes: str = "",
        reviewer_id: str = "",
    ) -> WorkflowSession:
        """
        Ferdigstiller gjennomgangen.

        Alle avvik må ha en beslutning før gjennomgangen kan fullføres.

        Args:
            session:                  WorkflowSession
            expected_deviation_ids:   Liste over alle avviks-IDer i saken
            summary_notes:            Overordnet oppsummering fra arkitekt
            reviewer_id:              ID til gjennomfører

        Returns:
            Oppdatert WorkflowSession med COMPLETED-tilstand

        Raises:
            IncompleteReviewError: Hvis ikke alle avvik har beslutning
            InvalidTransitionError: Hvis ikke i IN_PROGRESS-tilstand
        """
        self._assert_valid_transition(session.state, ReviewState.COMPLETED)

        # Kontroller at alle avvik har beslutning
        missing = [
            dev_id for dev_id in expected_deviation_ids
            if dev_id not in session.deviation_decisions
        ]
        if missing:
            raise IncompleteReviewError(
                f"Følgende avvik mangler beslutning: {missing}. "
                f"Alle avvik må vurderes før gjennomgangen kan fullføres."
            )

        session.state = ReviewState.COMPLETED
        session.summary_notes = summary_notes
        session.completed_at = datetime.now(tz=timezone.utc).isoformat()
        session.audit_log.append(AuditEntry(
            actor_id=reviewer_id or session.reviewer_id,
            action="complete_review",
            details={
                "total_decisions": len(session.deviation_decisions),
                "confirmed": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.CONFIRMED
                ),
                "dismissed": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.DISMISSED
                ),
                "requires_action": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.REQUIRES_ACTION
                ),
            },
        ))
        logger.info(
            "Gjennomgang %s fullført. %d avvik vurdert.",
            session.review_id,
            len(session.deviation_decisions),
        )
        return session

    def reject_review(
        self,
        session: WorkflowSession,
        reason: str,
        reviewer_id: str = "",
    ) -> WorkflowSession:
        """Avviser gjennomgangen med begrunnelse."""
        self._assert_valid_transition(session.state, ReviewState.REJECTED)
        session.state = ReviewState.REJECTED
        session.audit_log.append(AuditEntry(
            actor_id=reviewer_id or session.reviewer_id,
            action="reject_review",
            details={"reason": reason},
        ))
        return session

    def reopen_review(
        self,
        session: WorkflowSession,
        reason: str,
        reviewer_id: str = "",
    ) -> WorkflowSession:
        """Gjenåpner en fullført eller avvist gjennomgang."""
        self._assert_valid_transition(session.state, ReviewState.IN_PROGRESS)
        previous_state = session.state
        session.state = ReviewState.IN_PROGRESS
        session.completed_at = None
        session.audit_log.append(AuditEntry(
            actor_id=reviewer_id or session.reviewer_id,
            action="reopen_review",
            details={"previous_state": previous_state.value, "reason": reason},
        ))
        return session

    def get_progress(self, session: WorkflowSession, total_deviations: int) -> dict:
        """Returnerer fremdriftsinformasjon for gjennomgangen."""
        decided = len(session.deviation_decisions)
        return {
            "state": session.state.value,
            "decided": decided,
            "total": total_deviations,
            "remaining": max(0, total_deviations - decided),
            "percent_complete": round(decided / total_deviations * 100) if total_deviations > 0 else 0,
            "decisions_summary": {
                "confirmed": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.CONFIRMED
                ),
                "dismissed": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.DISMISSED
                ),
                "requires_action": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.REQUIRES_ACTION
                ),
                "noted": sum(
                    1 for d in session.deviation_decisions.values()
                    if d.decision == DeviationDecision.NOTED
                ),
            },
        }

    def _assert_valid_transition(
        self, current: ReviewState, target: ReviewState
    ) -> None:
        allowed = self._VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Ugyldig tilstandsovergang: {current} → {target}. "
                f"Tillatte overganger fra {current}: {[s.value for s in allowed]}"
            )
