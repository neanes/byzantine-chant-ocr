from interpretation_options import InterpretationOptions
from analysis_models import ContourMatch, PageAnalysis


class AugmentedContourMatch(ContourMatch):
    def __init__(self, match: ContourMatch | None = None):
        super().__init__()
        self.is_base: bool = False
        self.is_martyria: bool = False
        self.is_kronos: bool = False

        if match is not None:
            self.__dict__.update(match.__dict__)


class NeumeGroup:
    def __init__(self):
        self.line: int = -1
        self.base: AugmentedContourMatch = AugmentedContourMatch()
        self.support: list[AugmentedContourMatch] = []


def is_base(label: str) -> bool:
    return label in [
        "ison",
        "oligon",
        "petaste",
        "apostrofos",
        "elafron",
        "elafron_apostrofos",
        "hamili",
        "vareia",
        "kentima",
        "yporroe",
        "stavros",
    ]


def is_fthora_martyria(label: str) -> bool:
    return label in ["fthora_hard_chromatic_di"]


def touches_baseline(match: ContourMatch, baseline: float) -> bool:
    return (
        match.bounding_rect.y
        <= baseline
        <= match.bounding_rect.y + match.bounding_rect.h
    )


def find_support(g: NeumeGroup, matches: list[AugmentedContourMatch], start_index: int):
    m = matches[start_index]

    # Find the supporting neumes to the right
    for i in range(start_index + 1, len(matches)):
        s = matches[i]

        # Stop if we are not on the same line number
        if s.line != m.line:
            break

        # Stop if the neumes are too far to the right
        # That is, the left edge is farther right than the right edge
        # of the base neume
        if s.bounding_rect.x > m.bounding_rect.x + m.bounding_rect.w:
            break

        g.support.append(s)

    # Find the supporting neumes to the left
    for i in range(start_index - 1, -1, -1):
        s = matches[i]

        # Stop if we are not on the same line number
        if s.line != m.line:
            break

        # Stop if the neumes are too far to the left
        # That is, the right edge is farther left than the left edge
        # of the base neume
        if s.bounding_rect.x + s.bounding_rect.w < m.bounding_rect.x:
            break

        # Ignore other base neumes
        if s.is_base:
            continue

        g.support.append(s)


def find_base(matches: list[AugmentedContourMatch], start_index: int):
    m = matches[start_index]

    # Search for a base to the right
    for i in range(start_index + 1, len(matches)):
        s = matches[i]

        # Stop if not on the same line
        if s.line != m.line:
            break

        # If we find a base, check whether it overlaps.
        # If it doesn't, stop searching.
        if s.is_base or is_base(s.label):
            if (
                s.bounding_rect.x
                <= m.bounding_circle.x
                <= s.bounding_rect.x + s.bounding_rect.w
            ):
                return s
            else:
                break

    # Search for a base to the left
    for i in range(start_index - 1, -1, -1):
        s = matches[i]

        # Stop if not on the same line
        if s.line != m.line:
            break

        # If we find a base, check whether it overlaps.
        # If it doesn't, stop searching.
        if s.is_base or is_base(s.label):
            if (
                s.bounding_rect.x
                <= m.bounding_circle.x
                <= s.bounding_rect.x + s.bounding_rect.w
            ):
                return s
            else:
                break

    # If no base found
    return None


def group_matches(
    analysis: PageAnalysis, options: InterpretationOptions
) -> list[NeumeGroup]:
    groups = []

    # Filter out bad matches and convert the remaining matches
    matches = [
        AugmentedContourMatch(x)
        for x in analysis.matches
        if x.line >= 0
        and x.label is not None
        and x.confidence > options.min_confidence_threshold
    ]

    # Form groups. There are three types of groups:
    # 1) Base neumes that touch the baseline
    # 2) Martyria
    # 3) Kronos

    for i, m in enumerate(matches):
        # TODO the condition "touches_baseline" can sometimes cause
        # true base neumes to be filtered out if, for example, a line contains a single
        # apostrofos followed by a hard chromatic martyria. This can cause the base line detection
        # to mistakenly place the base line lower than it should.
        m.is_base = is_base(m.label) and touches_baseline(
            m, analysis.segmentation.baselines[m.line]
        )

        # Handle double apostrofos
        if (
            not m.is_base
            and m.label == "apostrofos"
            and len(groups) > 0
            and groups[-1].base.label == "apostrofos"
            and m not in groups[-1].support
            and abs(
                m.bounding_rect.y
                - (groups[-1].base.bounding_rect.y + groups[-1].base.bounding_rect.h)
            )
            < analysis.segmentation.oligon_height
        ):
            m.is_base = True

        # Breath sign with no base
        if not m.is_base and m.label == "breath" and not find_base(matches, i):
            m.is_base = True

        # Martyria detection
        m.is_martyria = (
            m.label.startswith("martyria")
            and not m.label.startswith("martyria_root")
            and m.confidence > options.martyria_confidence_threshold
        )

        # Kronos detection
        m.is_kronos = m.label == "kronos"

        if m.is_base:
            g = NeumeGroup()
            g.line = m.line
            groups.append(g)
            g.base = m
            find_support(g, matches, i)

        elif m.is_martyria or m.is_kronos:
            # Only trust this prediction if there is no base neume above or below
            if not find_base(matches, i):
                g = NeumeGroup()
                g.line = m.line
                g.base = m
                find_support(g, matches, i)
                groups.append(g)
        elif (
            is_fthora_martyria(m.label)
            and m.confidence > options.martyria_confidence_threshold
        ):
            # Handle ambiguous fthora/martyria cases.
            # If this match is neume that could be both a martyria
            # or a fthora, we must check its support. If it has
            # base in the support, then it's a fthora. Otherwise it is a
            # martyria.
            if not find_base(matches, i):
                g = NeumeGroup()
                g.line = m.line
                g.base = m
                m.is_martyria = True
                find_support(g, matches, i)
                groups.append(g)

    return groups
