from enum import Enum
from dataclasses import dataclass, field

from e2e_models import EmptyElement, NoteElement


class IssueType(Enum):
    ACCIDENTAL = "accidental"
    BASE_SUBSTITUTION = "base_substitution"
    FTHORA = "fthora"
    GORGON = "gorgon"
    QUALITY = "quality"
    TIME = "time"
    VAREIA = "vareia"


@dataclass
class Issue:
    type: IssueType
    expected: str
    actual: str


@dataclass
class ElementWithIssues:
    actual_index: int
    expected_index: int
    expected_base: str
    issues: list[Issue] = field(default_factory=list)

    @classmethod
    def from_elements(cls, expected: NoteElement, actual: NoteElement, issues):
        return cls(
            actual_index=actual.index,
            expected_index=expected.index,
            expected_base=expected.neume,
            # ocr_neume_group=getattr(actual, "ocr_neume_group", None),
            issues=issues,
        )


@dataclass
class Scores:
    gorgon: int = 0
    quality: int = 0
    vareia: int = 0
    time: int = 0
    accidental: int = 0
    fthora: int = 0

    @property
    def total(self) -> int:
        return self.gorgon + self.quality + self.vareia + self.time


def score(
    expected: NoteElement, actual: NoteElement, penalties: Scores, totals: Scores
) -> list[Issue]:
    issues = []

    # Gorgon
    if expected.gorgon is not None or actual.gorgon is not None:
        totals.gorgon += 1

    if expected.gorgon != actual.gorgon:
        penalties.gorgon += 1
        issues.append(Issue(IssueType.GORGON, expected.gorgon, actual.gorgon))

    # Quality / Vocal expression
    if expected.quality is not None or actual.quality is not None:
        totals.quality += 1

    if expected.quality != actual.quality:
        penalties.quality += 1
        issues.append(
            Issue(
                IssueType.QUALITY,
                expected.quality,
                actual.quality,
            )
        )

    # Time
    if expected.time is not None or actual.time is not None:
        totals.time += 1

    if expected.time != actual.time:
        penalties.time += 1
        issues.append(Issue(IssueType.TIME, expected.time, actual.time))

    # Accidentals
    if expected.accidental is not None or actual.accidental is not None:
        totals.accidental += 1

    if expected.accidental != actual.accidental:
        penalties.accidental += 1
        issues.append(
            Issue(IssueType.ACCIDENTAL, expected.accidental, actual.accidental)
        )

    # Fthora
    if expected.fthora is not None or actual.fthora is not None:
        totals.fthora += 1

    if expected.fthora != actual.fthora:
        penalties.fthora += 1
        issues.append(Issue(IssueType.FTHORA, expected.fthora, actual.fthora))

    # Vareia
    if expected.vareia or actual.vareia:
        totals.vareia += 1

    if expected.vareia != actual.vareia:
        penalties.vareia += 1
        issues.append(Issue(IssueType.VAREIA, expected.vareia, actual.vareia))

    return issues


def calculate_scorecard(
    expected_elements: list[NoteElement | EmptyElement],
    actual_elements: list[NoteElement | EmptyElement],
):
    penalties = Scores()
    totals = Scores()
    elements_with_issues: list[ElementWithIssues] = []

    for expected, actual in zip(expected_elements, actual_elements):

        if isinstance(expected, EmptyElement) or isinstance(actual, EmptyElement):
            continue

        issues = score(expected, actual, penalties, totals)

        # Base substitution
        if expected.neume != actual.neume:
            issues.append(
                Issue(
                    IssueType.BASE_SUBSTITUTION,
                    expected.neume,
                    actual.neume,
                )
            )

        if issues:
            elements_with_issues.append(
                ElementWithIssues.from_elements(expected, actual, issues)
            )

    similarities = Scores()

    # Avoid div-by-zero errors
    def safe_ratio(x, total):
        return 1 - (x / total) if total > 0 else 1.0

    similarities.gorgon = safe_ratio(penalties.gorgon, totals.gorgon)
    similarities.time = safe_ratio(penalties.time, totals.time)
    similarities.vareia = safe_ratio(penalties.vareia, totals.vareia)
    similarities.quality = safe_ratio(penalties.quality, totals.quality)
    similarities.accidental = safe_ratio(penalties.accidental, totals.accidental)
    similarities.fthora = safe_ratio(penalties.fthora, totals.fthora)

    similarity = safe_ratio(penalties.total, totals.total)

    return {
        "penalties": penalties,
        "totals": totals,
        "similarities": similarities,
        "similarity": similarity,
        "elements_with_issues": elements_with_issues,
    }
