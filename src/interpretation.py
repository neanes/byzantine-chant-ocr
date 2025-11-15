from grouping import AugmentedContourMatch, NeumeGroup, group_matches
from interpretation_options import InterpretationOptions
from neumes import (
    Accidental,
    Fthora,
    GorgonNeume,
    QuantitativeNeume,
    TempoSign,
    TimeNeume,
    VocalExpressionNeume,
)
from ocr import ContourMatch, PageAnalysis
from segmentation import Segmentation


class InterpretedNeumeGroup:
    def __init__(self):
        self.id: int = -1
        self.ocr_neume_group: NeumeGroup | None = None

    def to_dict(self):
        d = {
            "id": self.id,
            "line": self.ocr_neume_group.line,
            "components": {
                "base": self.ocr_neume_group.base.id,
                **(
                    {"support": [x.id for x in self.ocr_neume_group.support]}
                    if len(self.ocr_neume_group.support)
                    else {}
                ),
            },
        }

        return {k: v for k, v in d.items() if v is not None}


class NoteGroup(InterpretedNeumeGroup):
    def __init__(self):
        super().__init__()
        self.quantitative_neume: QuantitativeNeume | None = None
        self.accidental: Accidental | None = None
        self.fthora: Fthora | None = None
        self.gorgon_neume: GorgonNeume | None = None
        self.time_neume: TimeNeume | None = None
        self.vocal_expression_neume: VocalExpressionNeume | None = None
        self.vareia: bool = False

    def to_dict(self):
        if self.quantitative_neume is None:
            print(self.ocr_neume_group.base.to_dict())
            for x in self.ocr_neume_group.support:
                print(x.to_dict())

        d = {
            **super().to_dict(),
            "type": "note",
            "neume": self.quantitative_neume.value,
            "accidental": self.accidental.value if self.accidental else None,
            "fthora": self.fthora.value if self.fthora else None,
            "gorgon": self.gorgon_neume.value if self.gorgon_neume else None,
            "time": self.time_neume.value if self.time_neume else None,
            "vocal_expression": (
                self.vocal_expression_neume.value
                if self.vocal_expression_neume
                else None
            ),
        }

        if self.vareia:
            d["vareia"] = True

        return {k: v for k, v in d.items() if v is not None}


class MartyriaGroup(InterpretedNeumeGroup):
    def __init__(self):
        super().__init__()
        self.fthora: Fthora | None = None

    def to_dict(self):
        d = {
            **super().to_dict(),
            "type": "martyria",
            "fthora": self.fthora.value if self.fthora else None,
        }

        return {k: v for k, v in d.items() if v is not None}


class TempoGroup(InterpretedNeumeGroup):
    def __init__(self):
        super().__init__()
        self.neume: TempoSign | None = None

    def to_dict(self):
        return {
            **super().to_dict(),
            "type": "tempo",
            "neume": self.neume.value,
        }


def interpret_page_analysis(analysis: PageAnalysis, options: InterpretationOptions):
    elements: list[InterpretedNeumeGroup] = []

    groups = group_matches(analysis, options)

    vareia = False

    for i in range(len(groups)):
        g = groups[i]

        prev = groups[i - 1] if i - 1 >= 0 else None
        next = groups[i + 1] if i + 1 < len(groups) else None
        next_next = groups[i + 2] if i + 2 < len(groups) else None

        apply_sanity_checks(g, analysis.segmentation)

        if g.base.is_base:
            e = NoteGroup()
            e.ocr_neume_group = g

            if g.base.label == "oligon":
                if (
                    next is not None
                    and next.base.line == g.base.line
                    and next.base.label == "kentima"
                    and (
                        next_next is None
                        or next_next.base.label != "kentima"
                        or next_next.base.line != g.base.line
                    )
                ):
                    # Combine the kentima with the oligon and skip ahead
                    g.support.extend(next.support)
                    i += 1
                    e.quantitative_neume = process_oligon_with_middle_kentima(g)
                else:
                    e.quantitative_neume = process_oligon(g)

            elif g.base.label == "ison":
                e.quantitative_neume = process_ison(g)

            elif g.base.label == "petaste":
                e.quantitative_neume = process_petaste(g)

            elif g.base.label == "apostrofos":
                e.quantitative_neume = process_apostrofos(g)

                if (
                    e.quantitative_neume == QuantitativeNeume.Apostrophos
                    and next is not None
                    and next.base.line == g.base.line
                    and next.base.label == "elafron"
                    and not has(next, "gorgon")
                    and (
                        next.base.bounding_rect.x
                        - (g.base.bounding_rect.x + g.base.bounding_rect.w)
                    )
                    <= analysis.segmentation.oligon_width
                ):
                    # Combine the apostrofos with the elafron
                    e.quantitative_neume = QuantitativeNeume.RunningElaphron
                    g.support.extend(next.support)
                    i += 1

                elif (
                    e.quantitative_neume == QuantitativeNeume.Apostrophos
                    and next is not None
                    and next.base.line == g.base.line
                    and next.base.label == "petaste"
                    and has_above(next, "elafron")
                ):
                    # Combine apostrofos + petasti+elafron
                    e.quantitative_neume = QuantitativeNeume.PetastiPlusRunningElaphron
                    g.support.extend(next.support)
                    i += 1

                elif (
                    e.quantitative_neume == QuantitativeNeume.Apostrophos
                    and next is not None
                    and next.base.line == g.base.line
                    and next.base.label == "apostrofos"
                    and abs(
                        next.base.bounding_rect.y
                        - (g.base.bounding_rect.y + g.base.bounding_rect.h)
                    )
                    < analysis.segmentation.oligon_height
                ):
                    # Double apostrofos
                    # Combine into a double apostrofos when the top of the next apostrofos is
                    # very close to the bottom of the previous apostrofos
                    e.quantitative_neume = QuantitativeNeume.DoubleApostrophos
                    g.support.extend(next.support)
                    i += 1

            elif g.base.label == "elafron_syndesmos":
                e.quantitative_neume = QuantitativeNeume.RunningElaphron

            elif g.base.label == "yporroe":
                e.quantitative_neume = QuantitativeNeume.Hyporoe

            elif g.base.label == "elafron":
                e.quantitative_neume = QuantitativeNeume.Elaphron

                apostrofos = find(g, "apostrofos")
                if apostrofos:
                    e.quantitative_neume = QuantitativeNeume.ElaphronPlusApostrophos
                    # Sometimes the apostrofos is double detected
                    if next is not None and next.base == apostrofos[0]:
                        g.support.extend(next.support)
                        i += 1

            elif g.base.label == "elafron_apostrofos":
                e.quantitative_neume = QuantitativeNeume.ElaphronPlusApostrophos
                apostrofos = find(g, "apostrofos")

                # Sometimes the apostrofos is double detected
                if apostrofos and next is not None and next.base == apostrofos[0]:
                    g.support.extend(next.support)
                    i += 1

            elif g.base.label == "hamili":
                e.quantitative_neume = process_hamili(g)

            elif g.base.label == "kentima":
                if (
                    next is not None
                    and next.base.line == g.base.line
                    and next.base.label == "kentima"
                ):
                    e.quantitative_neume = QuantitativeNeume.Kentemata
                    g.support.extend(next.support)
                    i += 1

            elif g.base.label == "vareia":
                # TODO detect additional apli
                # if (has(g, 'apli', 0.1)) {
                #   e.quantitativeNeume = QuantitativeNeume.VareiaDotted;
                #   apply_gorgon(e, g);
                #   elements.push(e);
                #   continue;
                # }
                vareia = True
                continue

            elif g.base.label == "stavros":
                e.quantitative_neume = QuantitativeNeume.Cross
                elements.append(e)
                continue

            elif g.base.label == "breath":
                e.quantitative_neume = QuantitativeNeume.Breath
                elements.append(e)
                continue

            # Apply modifiers
            apply_antikenoma(e, g)
            apply_gorgon(e, g)
            apply_digorgon(e, g)
            apply_trigorgon(e, g)
            apply_apli(e, g)
            apply_klasma(e, g)
            apply_fthora(e, g)
            apply_accidental(e, g)
            apply_psifiston(e, g)
            apply_heteron(e, g)
            apply_homalon(e, g)
            apply_endofonon(e, g)
            apply_stavros(e, g)

            if vareia:
                e.vareia = True
                vareia = False

            if e.quantitative_neume is not None:
                elements.append(e)

        elif g.base.is_martyria:
            # TODO make this smarter
            e = MartyriaGroup()
            e.ocr_neume_group = g
            elements.append(e)

            apply_fthora(e, g)

        elif g.base.is_kronos:
            e = TempoGroup()
            e.ocr_neume_group = g
            elements.append(e)

            if has(g, "gorgon") and has(g, "argon"):
                e.neume = TempoSign.Medium
            elif has(g, "gorgon"):
                e.neume = TempoSign.Quick
            elif has(g, "digorgon"):
                e.neume = TempoSign.Quicker
            elif has(g, "trigorgon"):
                e.neume = TempoSign.VeryQuick
            elif has(g, "argon"):
                e.neume = TempoSign.Moderate
            elif has(g, "diargon"):
                e.neume = TempoSign.Slow
            elif has(g, "triargon"):
                e.neume = TempoSign.Slower

    analysis.interpreted_groups = elements

    for i, e in enumerate(elements):
        e.id = i


def touches_baseline(match: ContourMatch, baseline: float) -> bool:
    return (
        match.bounding_rect.y
        <= baseline
        <= match.bounding_rect.y + match.bounding_rect.h
    )


def touches_any_textline(match: ContourMatch, textlines: list[float]) -> bool:
    return any(
        match.bounding_rect.y <= y <= match.bounding_rect.y + match.bounding_rect.h
        for y in textlines
    )


def center_overlaps(
    base: AugmentedContourMatch, support: AugmentedContourMatch
) -> bool:
    return (
        base.bounding_rect.x
        <= support.bounding_circle.x
        <= base.bounding_rect.x + base.bounding_rect.w
    )


def left_overlaps(base: AugmentedContourMatch, support: AugmentedContourMatch) -> bool:
    return (
        base.bounding_rect.x
        <= support.bounding_rect.x
        <= base.bounding_rect.x + base.bounding_rect.w
    )


def overlaps(base: ContourMatch, support: ContourMatch, threshold: float) -> bool:
    left = max(base.bounding_rect.x, support.bounding_rect.x)
    right = min(
        base.bounding_rect.x + base.bounding_rect.w,
        support.bounding_rect.x + support.bounding_rect.w,
    )
    return (right - left) / support.bounding_rect.w >= threshold


def find_above(
    g: NeumeGroup, label: str, threshold: float = 1.0
) -> list[AugmentedContourMatch]:
    return [
        x
        for x in g.support
        if x.bounding_circle.y < g.base.bounding_circle.y
        and x.label == label
        and (center_overlaps(g.base, x) or overlaps(g.base, x, threshold))
    ]


def find_below(
    g: NeumeGroup, label: str, threshold: float = 1.0
) -> list[AugmentedContourMatch]:
    return [
        x
        for x in g.support
        if x.bounding_circle.y > g.base.bounding_circle.y
        and x.label == label
        and (center_overlaps(g.base, x) or overlaps(g.base, x, threshold))
    ]


def find(
    g: NeumeGroup, label: str, threshold: float = 1.0
) -> list[AugmentedContourMatch]:
    return [
        x
        for x in g.support
        if x.label == label
        and (center_overlaps(g.base, x) or overlaps(g.base, x, threshold))
    ]


def has_above(g: NeumeGroup, label: str, threshold: float = 1.0) -> bool:
    return len(find_above(g, label, threshold)) > 0


def has_below(g: NeumeGroup, label: str, threshold: float = 1.0) -> bool:
    return len(find_below(g, label, threshold)) > 0


def has(g: NeumeGroup, label: str, threshold: float = 1.0) -> bool:
    return len(find(g, label, threshold)) > 0


def apply_sanity_checks(g: NeumeGroup, segmentation: Segmentation):
    def confidence(matches: list[AugmentedContourMatch]) -> float:
        return max(x.confidence for x in matches)

    # Filter out apli that are too low
    for x in find_below(g, "apli"):
        if (
            x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h)
            >= 2 * segmentation.oligon_height
        ):
            g.support.remove(x)

    # Filter out kentimata that are too low
    for x in find_below(g, "kentima"):
        if (
            x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h)
            >= 2 * segmentation.oligon_height
        ):
            g.support.remove(x)

    # Filter out gorgons that are too high
    for x in find_above(g, "gorgon"):
        if (
            g.base.bounding_rect.y - (x.bounding_rect.y + x.bounding_rect.h)
            > 0.75 * segmentation.oligon_width
        ):
            g.support.remove(x)

    # Filter out kentima that are too high
    for x in find_above(g, "kentima"):
        if (
            g.base.bounding_rect.y - (x.bounding_rect.y + x.bounding_rect.h)
            > 0.75 * segmentation.oligon_width
        ):
            g.support.remove(x)

    # Filter out gorgon that are too low
    for x in find_below(g, "gorgon"):
        if (
            x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h)
            >= 2 * segmentation.oligon_height
        ):
            g.support.remove(x)

    # If there is both a klasma and apli, use confidence as tie breaker
    apli = find_below(g, "apli")
    klasma = find(g, "klasma")
    if apli and klasma:
        if confidence(klasma) > confidence(apli):
            g.support = [x for x in g.support if x.label != "apli"]
        else:
            g.support = [x for x in g.support if x.label != "klasma"]

    # If the group has both a gorgon and klasma,
    # this is probably wrong. So take the highest confidence only.
    gorgon = find(g, "gorgon")
    klasma = find(g, "klasma")
    if gorgon and klasma:
        if confidence(klasma) > confidence(gorgon):
            g.support = [x for x in g.support if x.label != "gorgon"]
        else:
            g.support = [x for x in g.support if x.label != "klasma"]

    # If the group has both a gorgon and apli below the neume,
    # this is probably wrong. So take the highest confidence only.
    apli = find_below(g, "apli")
    gorgon = find_below(g, "gorgon")
    if gorgon and apli:
        if confidence(apli) > confidence(gorgon):
            g.support = [x for x in g.support if x.label != "gorgon"]
        else:
            g.support = [x for x in g.support if x.label != "apli"]

    # If the group has both a gorgon/apli and psifiston,
    # this is probably wrong. So take the highest confidence only.
    psifiston = find_below(g, "psifiston")
    gorgon = find(g, "gorgon")
    if psifiston and gorgon:
        if confidence(psifiston) > confidence(gorgon):
            g.support = [x for x in g.support if x.label != "gorgon"]
        else:
            g.support = [x for x in g.support if x.label != "psifiston"]

    psifiston = find_below(g, "psifiston")
    apli = find_below(g, "apli")
    if psifiston and apli:
        if confidence(psifiston) > confidence(apli):
            g.support = [x for x in g.support if x.label != "apli"]
        else:
            g.support = [x for x in g.support if x.label != "psifiston"]

    # Filter out sharps that are too low
    for sharp_label in ["sharp_2", "sharp_4", "general_sharp"]:
        for x in find_below(g, sharp_label):
            if touches_any_textline(x, segmentation.textlines_adj):
                g.support.remove(x)


def apply_antikenoma(e: NoteGroup, g: NeumeGroup):
    if has_below(g, "antikenoma", 0.5):
        e.vocal_expression_neume = VocalExpressionNeume.Antikenoma
    elif has_below(g, "antikenoma_apli", 0.5):
        e.vocal_expression_neume = VocalExpressionNeume.Antikenoma
        e.time_neume = TimeNeume.Hapli


def apply_gorgon(e: NoteGroup, g: NeumeGroup):
    gorgons = [
        x
        for x in g.support
        if x.label == "gorgon"
        and (
            left_overlaps(g.base, x)
            or overlaps(g.base, x, 0.9)
            or center_overlaps(g.base, x)
        )
    ]

    # TODO secondary/tertiary gorgons

    for gorgon in gorgons:
        # TODO this parentheses logic needs to be more precise
        paren_left = find_above(g, "paren_left")
        paren_right = find_above(g, "paren_right")

        above = gorgon.bounding_circle.y <= g.base.bounding_circle.y

        if (
            above
            and paren_left
            and paren_left[0].bounding_circle.x < gorgon.bounding_circle.x
        ):
            return

        if (
            above
            and paren_right
            and paren_right[0].bounding_circle.x > gorgon.bounding_circle.x
        ):
            return

        e.gorgon_neume = GorgonNeume.Gorgon_Top if above else GorgonNeume.Gorgon_Bottom

        # Take the first gorgon we find that is not actually an ison indicator
        break


def apply_digorgon(e: NoteGroup, g: NeumeGroup):
    # TODO secondary/tertiary gorgons
    if has_above(g, "digorgon", 0.8):
        e.gorgon_neume = GorgonNeume.Digorgon


def apply_trigorgon(e: NoteGroup, g: NeumeGroup):
    # TODO secondary/tertiary gorgons
    if has_above(g, "trigorgon", 0.8):
        e.gorgon_neume = GorgonNeume.Trigorgon


def apply_klasma(e: NoteGroup, g: NeumeGroup):
    klasma = find(g, "klasma", 0.8)
    if klasma:
        e.time_neume = (
            TimeNeume.Klasma_Top
            if klasma[0].bounding_circle.y <= g.base.bounding_circle.y
            else TimeNeume.Klasma_Bottom
        )


def apply_apli(e: NoteGroup, g: NeumeGroup):
    apli = find_below(g, "apli")
    if len(apli) == 1:
        e.time_neume = TimeNeume.Hapli
    elif len(apli) == 2:
        e.time_neume = TimeNeume.Dipli
    elif len(apli) == 3:
        e.time_neume = TimeNeume.Tripli
    elif len(apli) >= 4:
        e.time_neume = TimeNeume.Tetrapli


def apply_fthora(e: NoteGroup | MartyriaGroup, g: NeumeGroup):
    fthoras = [x for x in g.support if x.label.startswith("fthora")]

    fthora = None

    # Find the fthora with the highest confidence
    for f in fthoras:
        if fthora is None or f.confidence > fthora.confidence:
            fthora = f

    # TODO secondary/tertiary gorgons
    if fthora and (overlaps(g.base, fthora, 0.8) or center_overlaps(g.base, fthora)):
        if fthora.bounding_rect.y < g.base.bounding_rect.y:
            top_map = {
                "fthora_diatonic_di": Fthora.DiatonicThi_Top,
                "fthora_diatonic_ke": Fthora.DiatonicKe_Top,
                "fthora_diatonic_ni": Fthora.DiatonicNiLow_Top,
                "fthora_diatonic_ni_high": Fthora.DiatonicNiHigh_Top,
                "fthora_diatonic_pa": Fthora.DiatonicPa_Top,
                "fthora_diatonic_vou": Fthora.DiatonicVou_Top,
                "fthora_enharmonic": Fthora.Enharmonic_Top,
                "fthora_hard_chromatic_di": Fthora.HardChromaticThi_Top,
                "fthora_hard_chromatic_pa": Fthora.HardChromaticPa_Top,
                "fthora_soft_chromatic_di": Fthora.SoftChromaticThi_Top,
                "fthora_zygos": Fthora.Zygos_Top,
            }
            e.fthora = top_map.get(fthora.label)
        else:
            bottom_map = {
                "fthora_diatonic_di": Fthora.DiatonicThi_Bottom,
                "fthora_diatonic_ke": Fthora.DiatonicKe_Bottom,
                "fthora_diatonic_ni": Fthora.DiatonicNiLow_Bottom,
                "fthora_diatonic_ni_high": Fthora.DiatonicNiHigh_Bottom,
                "fthora_diatonic_pa": Fthora.DiatonicPa_Bottom,
                "fthora_diatonic_vou": Fthora.DiatonicVou_Bottom,
                "fthora_enharmonic": Fthora.Enharmonic_Bottom,
                "fthora_hard_chromatic_di": Fthora.HardChromaticThi_Bottom,
                "fthora_hard_chromatic_pa": Fthora.HardChromaticPa_Bottom,
                "fthora_soft_chromatic_di": Fthora.SoftChromaticThi_Bottom,
                "fthora_zygos": Fthora.Zygos_Bottom,
            }
            e.fthora = bottom_map.get(fthora.label)


def apply_accidental(e: NoteGroup, g: NeumeGroup):
    if has_below(g, "sharp_2", 0.5):
        e.accidental = Accidental.Sharp_2_Left
    elif has_below(g, "sharp_4", 0.5):
        e.accidental = Accidental.Sharp_4_Left
    elif has_below(g, "sharp_general"):
        e.fthora = Fthora.GeneralSharp_Bottom
    elif has_above(g, "sharp_general"):
        e.fthora = Fthora.GeneralSharp_Top
    elif has_above(g, "flat_2", 0.5):
        e.accidental = Accidental.Flat_2_Right
    elif has_above(g, "flat_4", 0.5):
        e.accidental = Accidental.Flat_4_Right
    elif has_above(g, "flat_general"):
        e.fthora = Fthora.GeneralFlat_Top


def apply_psifiston(e: NoteGroup, g: NeumeGroup):
    if has_below(g, "psifiston", 0.75):
        e.vocal_expression_neume = VocalExpressionNeume.Psifiston


def apply_heteron(e: NoteGroup, g: NeumeGroup):
    heteron = find_below(g, "heteron", 0)
    if heteron and heteron[0].bounding_rect.x > g.base.bounding_rect.x:
        # TODO figure out if it's connecting or not
        # Probably need to be able to detect apli before we can do this.
        e.vocal_expression_neume = VocalExpressionNeume.HeteronConnecting


def apply_homalon(e: NoteGroup, g: NeumeGroup):
    homalon = find_below(g, "omalon", 0)
    if homalon and homalon[0].bounding_rect.x > g.base.bounding_rect.x:
        if has_above(g, "klasma"):
            e.vocal_expression_neume = VocalExpressionNeume.Homalon
        else:
            e.vocal_expression_neume = VocalExpressionNeume.HomalonConnecting


def apply_endofonon(e: NoteGroup, g: NeumeGroup):
    endofonon = find_below(g, "endofonon", 0)
    if endofonon and endofonon[0].bounding_rect.x > g.base.bounding_rect.x:
        e.vocal_expression_neume = VocalExpressionNeume.Endofonon


def apply_stavros(e: NoteGroup, g: NeumeGroup):
    if has(g, "stavros", 0):
        e.vocal_expression_neume = VocalExpressionNeume.Cross_Top


def process_ison(g: NeumeGroup):
    if has(g, "apostrofos"):
        return QuantitativeNeume.IsonPlusApostrophos
    return QuantitativeNeume.Ison


def process_apostrofos(g: NeumeGroup):
    if has(g, "apostrofos"):
        return QuantitativeNeume.DoubleApostrophos
    return QuantitativeNeume.Apostrophos


def process_oligon(g: NeumeGroup):
    kentima_below = find_below(g, "kentima", 0.9)
    if len(kentima_below) == 1:
        return QuantitativeNeume.OligonPlusKentimaBelow
    if len(kentima_below) >= 2:
        return QuantitativeNeume.KentemataPlusOligon

    kentima_above = find_above(g, "kentima", 0.1)

    # Handle oligon + kentemata
    # If at least one kentima was found and we find ison, apostrofos, elafron, etc.
    # Then we assume that there is a second kentima, even if it wasn't detected.
    if len(kentima_above) >= 1:
        if has_above(g, "ison"):
            return QuantitativeNeume.OligonPlusIsonPlusKentemata

        apostrofos_above = find_above(g, "apostrofos", 0.1)
        elafron_above = find_above(g, "elafron")
        has_elafron_apostrofos_above = has_above(g, "elafron_apostrofos")

        has_apostrofos_above = len(apostrofos_above) > 0
        has_elafron_above = len(elafron_above) > 0

        if has_apostrofos_above and not has_elafron_above:
            return QuantitativeNeume.OligonPlusApostrophosPlusKentemata
        if not has_apostrofos_above and has_elafron_above:
            return QuantitativeNeume.OligonPlusElaphronPlusKentemata
        if has_elafron_apostrofos_above:
            return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata
        if has_above(g, "elafron_syndesmos", 0.8):
            return QuantitativeNeume.OligonPlusRunningElaphronPlusKentemata

        # Sometimes OCR detects elafron_apostrofos as one character,
        # sometimes as two. So this may be a running elafron.
        if has_apostrofos_above and has_elafron_above:
            if apostrofos_above[0].bounding_rect.x < elafron_above[0].bounding_rect.x:
                return QuantitativeNeume.OligonPlusRunningElaphronPlusKentemata
            return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata

        if has_above(g, "yporroe"):
            return QuantitativeNeume.OligonPlusHyporoePlusKentemata
        if has_above(g, "hamili"):
            return QuantitativeNeume.OligonPlusHamiliPlusKentemata

    if len(kentima_above) >= 2:
        ypsili = find_above(g, "ypsili")
        if len(ypsili) == 1:
            neume = ypsili[0]
            left = abs(neume.bounding_circle.x - g.base.bounding_rect.x)
            right = abs(
                neume.bounding_circle.x
                - (g.base.bounding_rect.x + g.base.bounding_rect.w)
            )
            return (
                QuantitativeNeume.OligonPlusKentemataPlusHypsiliLeft
                if left < right
                else QuantitativeNeume.OligonPlusKentemataPlusHypsiliRight
            )
        if len(ypsili) == 2:
            return QuantitativeNeume.OligonKentimataDoubleYpsili
        if len(ypsili) >= 3:
            return QuantitativeNeume.OligonKentimataTripleYpsili
        return QuantitativeNeume.OligonPlusKentemata

    # Handle oligon with single kentima
    if len(kentima_above) == 1:
        ypsili = find_above(g, "ypsili")
        if len(ypsili) == 1:
            neume = ypsili[0]
            left = abs(neume.bounding_circle.x - g.base.bounding_rect.x)
            right = abs(
                neume.bounding_circle.x
                - (g.base.bounding_rect.x + g.base.bounding_rect.w)
            )
            return (
                QuantitativeNeume.OligonPlusHypsiliPlusKentimaVertical
                if left < right
                else QuantitativeNeume.OligonPlusHypsiliPlusKentimaHorizontal
            )
        if len(ypsili) == 2:
            if any(
                x.bounding_rect.x
                < g.base.bounding_circle.x - g.base.bounding_rect.w / 4
                for x in ypsili
            ):
                return QuantitativeNeume.OligonKentimaDoubleYpsiliLeft
            return QuantitativeNeume.OligonKentimaDoubleYpsiliRight
        if len(ypsili) >= 3:
            return QuantitativeNeume.OligonKentimaTripleYpsili
        return QuantitativeNeume.OligonPlusKentimaAbove

    # Check for ypsili
    ypsili = find_above(g, "ypsili")
    if len(ypsili) == 1:
        neume = ypsili[0]
        left = abs(neume.bounding_circle.x - g.base.bounding_rect.x)
        right = abs(
            neume.bounding_circle.x - (g.base.bounding_rect.x + g.base.bounding_rect.w)
        )
        return (
            QuantitativeNeume.OligonPlusHypsiliLeft
            if left < right
            else QuantitativeNeume.OligonPlusHypsiliRight
        )
    if len(ypsili) == 2:
        return QuantitativeNeume.OligonPlusDoubleHypsili
    if len(ypsili) >= 3:
        return QuantitativeNeume.OligonTripleYpsili

    if has_above(g, "ison"):
        return QuantitativeNeume.OligonPlusIson
    if has_above(g, "yporroe"):
        return QuantitativeNeume.OligonPlusHyporoe

    apostrofos_above = has_above(g, "apostrofos")
    elafron_above = has_above(g, "elafron")
    elafron_apostrofos_above = has_above(g, "elafron_apostrofos")

    if apostrofos_above and not elafron_above:
        return QuantitativeNeume.OligonPlusApostrophos
    if not apostrofos_above and elafron_above:
        return QuantitativeNeume.OligonPlusElaphron
    if elafron_apostrofos_above or (elafron_above and apostrofos_above):
        return QuantitativeNeume.OligonPlusElaphronPlusApostrophos
    if has_above(g, "hamili"):
        return QuantitativeNeume.OligonPlusHamili

    return QuantitativeNeume.Oligon


def process_oligon_with_middle_kentima(g: NeumeGroup):
    kentima_above = find_above(g, "kentima")

    # Handle oligon + kentemata
    if len(kentima_above) >= 2:
        return QuantitativeNeume.OligonKentimaMiddleKentimata
    return QuantitativeNeume.OligonPlusKentima


def process_petaste(g: NeumeGroup):
    kentima_above = find_above(g, "kentima")

    # Handle petaste + ypsili + kentemata
    if len(kentima_above) >= 2:
        ypsili = find_above(g, "ypsili")
        if len(ypsili) == 2:
            return QuantitativeNeume.PetastiKentimataDoubleYpsili
        if len(ypsili) >= 3:
            return QuantitativeNeume.PetastiKentimataTripleYpsili

    # Handle petaste with single kentima
    if len(kentima_above) == 1:
        ypsili = find_above(g, "ypsili")
        if len(ypsili) == 1:
            neume = ypsili[0]
            left = abs(neume.bounding_circle.x - g.base.bounding_rect.x)
            right = abs(
                neume.bounding_circle.x
                - (g.base.bounding_rect.x + g.base.bounding_rect.w)
            )
            return (
                QuantitativeNeume.PetastiPlusHypsiliPlusKentimaVertical
                if left < right
                else QuantitativeNeume.PetastiPlusHypsiliPlusKentimaHorizontal
            )
        if len(ypsili) == 2:
            if any(
                x.bounding_rect.x
                < g.base.bounding_circle.x - g.base.bounding_rect.w / 4
                for x in ypsili
            ):
                return QuantitativeNeume.PetastiKentimaDoubleYpsiliLeft
            return QuantitativeNeume.PetastiKentimaDoubleYpsiliRight
        if len(ypsili) >= 3:
            return QuantitativeNeume.PetastiKentimaTripleYpsili
        return QuantitativeNeume.PetastiPlusKentimaAbove

    # Check for ypsili
    ypsili = find_above(g, "ypsili")
    if len(ypsili) == 1:
        neume = ypsili[0]
        left = abs(neume.bounding_circle.x - g.base.bounding_rect.x)
        right = abs(
            neume.bounding_circle.x - (g.base.bounding_rect.x + g.base.bounding_rect.w)
        )
        return (
            QuantitativeNeume.PetastiPlusHypsiliLeft
            if left < right
            else QuantitativeNeume.PetastiPlusHypsiliRight
        )
    if len(ypsili) == 2:
        return QuantitativeNeume.PetastiPlusDoubleHypsili
    if len(ypsili) >= 3:
        return QuantitativeNeume.PetastiTripleYpsili

    # Check for petaste used as support
    if has_above(g, "ison", 0.9):
        return QuantitativeNeume.PetastiWithIson
    if has_above(g, "oligon", 0.9):
        return QuantitativeNeume.PetastiPlusOligon
    if has_above(g, "yporroe"):
        return QuantitativeNeume.PetastiPlusHyporoe

    hamili = find_above(g, "hamili")
    if len(hamili) == 1:
        apostrofos = has(g, "apostrofos")
        elafron = has(g, "elafron")
        elafron_apostrofos = has(g, "elafron_apostrofos")

        if apostrofos and not elafron:
            return QuantitativeNeume.PetastiHamiliApostrofos
        if not apostrofos and elafron:
            return QuantitativeNeume.PetastiHamiliElafron
        if (apostrofos and elafron) or elafron_apostrofos:
            return QuantitativeNeume.PetastiHamiliElafronApostrofos
        return QuantitativeNeume.PetastiHamili

    if len(hamili) >= 2:
        if has(g, "apostrofos"):
            return QuantitativeNeume.PetastiDoubleHamiliApostrofos
        return QuantitativeNeume.PetastiDoubleHamili

    apostrofos_above = has_above(g, "apostrofos")
    elafron_above = has_above(g, "elafron")
    elafron_apostrofos_above = has_above(g, "elafron_apostrofos")

    if apostrofos_above and not elafron_above:
        return QuantitativeNeume.PetastiPlusApostrophos
    if not apostrofos_above and elafron_above:
        return QuantitativeNeume.PetastiPlusElaphron
    if elafron_apostrofos_above or (elafron_above and apostrofos_above):
        return QuantitativeNeume.PetastiPlusElaphronPlusApostrophos

    return QuantitativeNeume.Petasti


def process_hamili(g: NeumeGroup):
    # Check for extra hamili
    hamili = find(g, "hamili")

    # Handle double hamili
    if len(hamili) == 1:
        apostrofos = has(g, "apostrofos")
        elafron = has(g, "elafron")
        elafron_apostrofos = has(g, "elafron_apostrofos")

        if apostrofos and not elafron:
            return QuantitativeNeume.DoubleHamiliApostrofos
        if not apostrofos and elafron:
            return QuantitativeNeume.DoubleHamiliElafron
        if (apostrofos and elafron) or elafron_apostrofos:
            return QuantitativeNeume.DoubleHamiliElafronApostrofos
        return QuantitativeNeume.DoubleHamili

    if len(hamili) >= 2:
        return QuantitativeNeume.TripleHamili

    apostrofos_above = has_above(g, "apostrofos")
    elafron_above = has_above(g, "elafron")
    elafron_apostrofos_above = has_above(g, "elafron_apostrofos")

    if apostrofos_above and not elafron_above:
        return QuantitativeNeume.HamiliPlusApostrophos
    if not apostrofos_above and elafron_above:
        return QuantitativeNeume.HamiliPlusElaphron
    if elafron_apostrofos_above or (elafron_above and apostrofos_above):
        return QuantitativeNeume.HamiliPlusElaphronPlusApostrophos

    return QuantitativeNeume.Hamili
