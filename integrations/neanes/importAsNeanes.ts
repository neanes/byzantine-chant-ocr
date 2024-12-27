import { promises as fs } from "fs";
import YAML from "yaml";
import { Score } from "./neanes/models/Score";
import {
  EmptyElement,
  MartyriaElement,
  NoteElement,
  ScoreElement,
} from "./neanes/models/Element";
import {
  Fthora,
  GorgonNeume,
  Neume,
  QuantitativeNeume,
  TimeNeume,
  VocalExpressionNeume,
} from "./neanes/models/Neumes";
import {
  AugmentedContourMatch,
  ContourLineGroup,
  NeumeGroup,
} from "./OcrImportCustomModels";
import {
  ContourMatch,
  OcrAnalysis,
  PageAnalysis,
  Segmentation,
} from "./OcrAnalysis";
import { SaveService } from "./neanes/services/SaveService";

// Blank score
const score = new Score();
const analysis: OcrAnalysis = YAML.parse(
  await fs.readFile("output.yaml", "utf8")
);

const min_confidence_threshold = 0.7;
const martyria_confidence_threshold = 0.8;

const elements = processAnalysis(
  analysis,
  min_confidence_threshold,
  martyria_confidence_threshold
);

// Remove the empty element
score.staff.elements.pop();

elements.forEach((x) => score.staff.elements.push(x));

// Final element
score.staff.elements.push(new EmptyElement());

await fs.writeFile(
  "output.byzx",
  JSON.stringify(SaveService.SaveScoreToJson(score))
);

function has_support(g: NeumeGroup, s: string[]) {
  return s.every((x) => g.support.some((y) => y.label === x));
}

function processIson(g: NeumeGroup) {
  if (has(g, "apostrofos")) {
    return QuantitativeNeume.IsonPlusApostrophos;
  }
  return QuantitativeNeume.Ison;
}

function processApostrofos(g: NeumeGroup) {
  if (has(g, "apostrofos")) {
    return QuantitativeNeume.DoubleApostrophos;
  }

  return QuantitativeNeume.Apostrophos;
}

function processOligon(g: NeumeGroup) {
  // Check kentima below
  const kentimaBelow = findBelow(g, "kentima");

  if (kentimaBelow.length === 1) {
    return QuantitativeNeume.OligonPlusKentimaBelow;
  }

  if (kentimaBelow.length >= 2) {
    return QuantitativeNeume.KentemataPlusOligon;
  }

  // Check kentima above
  const kentimaAbove = findAbove(g, "kentima");

  // Handle oligon + kentemata
  if (kentimaAbove.length >= 2) {
    if (hasAbove(g, "ison")) {
      return QuantitativeNeume.OligonPlusIsonPlusKentemata;
    }

    const apostrofosAbove = findAbove(g, "apostrofos");
    const elafronAbove = findAbove(g, "elafron");
    const hasElafronApostrofosAbove = hasAbove(g, "elafron_apostrofos");

    const hasApostrofosAbove = apostrofosAbove.length > 0;
    const hasElafronAbove = elafronAbove.length > 0;

    if (hasApostrofosAbove && !hasElafronAbove) {
      return QuantitativeNeume.OligonPlusApostrophosPlusKentemata;
    }

    if (!hasApostrofosAbove && hasElafronAbove) {
      return QuantitativeNeume.OligonPlusElaphronPlusKentemata;
    }

    if (hasElafronApostrofosAbove) {
      return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata;
    }

    // Sometimes OCR detects elafron_apostrofos as one character,
    // sometimes as two. So this may be a running elafron.
    if (hasApostrofosAbove && hasElafronAbove) {
      if (
        apostrofosAbove[0].bounding_rect.x < elafronAbove[0].bounding_rect.x
      ) {
        return QuantitativeNeume.OligonPlusRunningElaphronPlusKentemata;
      }
      return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata;
    }

    if (hasAbove(g, "yporroe")) {
      return QuantitativeNeume.OligonPlusHyporoePlusKentemata;
    }

    if (hasAbove(g, "hamili")) {
      return QuantitativeNeume.OligonPlusHamiliPlusKentemata;
    }

    const ypsili = findAbove(g, "ypsili");

    if (ypsili.length === 1) {
      if (
        Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
        Math.abs(
          ypsili[0].bounding_circle.x -
            (g.base.bounding_rect.x + g.base.bounding_rect.w)
        )
      ) {
        return QuantitativeNeume.OligonPlusKentemataPlusHypsiliLeft;
      } else {
        return QuantitativeNeume.OligonPlusKentemataPlusHypsiliRight;
      }
    }

    if (ypsili.length === 2) {
      return QuantitativeNeume.OligonKentimataDoubleYpsili;
    }

    if (ypsili.length >= 3) {
      return QuantitativeNeume.OligonKentimataTripleYpsili;
    }

    return QuantitativeNeume.OligonPlusKentemata;
  }

  // Handle oligon with single kentima
  if (kentimaAbove.length == 1) {
    const ypsili = findAbove(g, "ypsili");

    if (ypsili.length === 1) {
      if (
        Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
        Math.abs(
          ypsili[0].bounding_circle.x -
            (g.base.bounding_rect.x + g.base.bounding_rect.w)
        )
      ) {
        return QuantitativeNeume.OligonPlusHypsiliPlusKentimaVertical;
      } else {
        return QuantitativeNeume.OligonPlusHypsiliPlusKentimaHorizontal;
      }
    }

    if (ypsili.length === 2) {
      if (
        ypsili.find(
          (x) =>
            x.bounding_rect.x <
            g.base.bounding_circle.x - g.base.bounding_rect.w / 4
        )
      ) {
        return QuantitativeNeume.OligonKentimaDoubleYpsiliLeft;
      }

      return QuantitativeNeume.OligonKentimaDoubleYpsiliRight;
    }

    if (ypsili.length >= 3) {
      return QuantitativeNeume.OligonKentimaTripleYpsili;
    }

    return QuantitativeNeume.OligonPlusKentimaAbove;
  }

  // Check for ypsili
  const ypsili = findAbove(g, "ypsili");

  if (ypsili.length === 1) {
    const neume = ypsili[0];

    if (
      Math.abs(neume.bounding_circle.x - g.base.bounding_rect.x) <
      Math.abs(
        neume.bounding_circle.x -
          (g.base.bounding_rect.x + g.base.bounding_rect.w)
      )
    ) {
      return QuantitativeNeume.OligonPlusHypsiliLeft;
    } else {
      return QuantitativeNeume.OligonPlusHypsiliRight;
    }
  }

  if (ypsili.length === 2) {
    return QuantitativeNeume.OligonPlusDoubleHypsili;
  }

  if (ypsili.length >= 3) {
    return QuantitativeNeume.OligonTripleYpsili;
  }

  // Check for oligon used as support
  if (hasAbove(g, "ison")) {
    return QuantitativeNeume.OligonPlusIson;
  }

  if (hasAbove(g, "apostrofos")) {
    return QuantitativeNeume.OligonPlusApostrophos;
  }

  if (hasAbove(g, "yporroe")) {
    return QuantitativeNeume.OligonPlusHyporoe;
  }

  const apostrofosAbove = hasAbove(g, "apostrofos");
  const elafronAbove = hasAbove(g, "elafron");
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos");

  if (apostrofosAbove && !elafronAbove) {
    return QuantitativeNeume.OligonPlusApostrophos;
  }

  if (!apostrofosAbove && elafronAbove) {
    return QuantitativeNeume.OligonPlusElaphron;
  }

  if (elafronApostrofosAbove || (elafronAbove && apostrofosAbove)) {
    return QuantitativeNeume.OligonPlusElaphronPlusApostrophos;
  }

  if (hasAbove(g, "hamili")) {
    return QuantitativeNeume.OligonPlusHamili;
  }

  return QuantitativeNeume.Oligon;
}

function processOligonWithMiddleKentima(g: NeumeGroup) {
  // Check kentima above
  const kentimaAbove = findAbove(g, "kentima");

  // Handle oligon + kentemata
  if (kentimaAbove.length >= 2) {
    return QuantitativeNeume.OligonKentimaMiddleKentimata;
  }

  return QuantitativeNeume.OligonPlusKentima;
}

function processPetaste(g: NeumeGroup) {
  // Check kentima above
  const kentimaAbove = findAbove(g, "kentima");

  // Handle petaste + ypsili + kentemata
  if (kentimaAbove.length >= 2) {
    const ypsili = findAbove(g, "ypsili");

    if (ypsili.length === 2) {
      return QuantitativeNeume.PetastiKentimataDoubleYpsili;
    }

    if (ypsili.length >= 3) {
      return QuantitativeNeume.PetastiKentimataTripleYpsili;
    }
  }

  // Handle petaste with single kentima
  if (kentimaAbove.length == 1) {
    const ypsili = findAbove(g, "ypsili");

    if (ypsili.length === 1) {
      if (
        Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
        Math.abs(
          ypsili[0].bounding_circle.x -
            (g.base.bounding_rect.x + g.base.bounding_rect.w)
        )
      ) {
        return QuantitativeNeume.PetastiPlusHypsiliPlusKentimaVertical;
      } else {
        return QuantitativeNeume.PetastiPlusHypsiliPlusKentimaHorizontal;
      }
    }

    if (ypsili.length === 2) {
      if (
        ypsili.find(
          (x) =>
            x.bounding_rect.x <
            g.base.bounding_circle.x - g.base.bounding_rect.w / 4
        )
      ) {
        return QuantitativeNeume.PetastiKentimaDoubleYpsiliLeft;
      }

      return QuantitativeNeume.PetastiKentimaDoubleYpsiliRight;
    }

    if (ypsili.length >= 3) {
      return QuantitativeNeume.PetastiKentimaTripleYpsili;
    }

    return QuantitativeNeume.PetastiPlusKentimaAbove;
  }

  // Check for ypsili
  const ypsili = findAbove(g, "ypsili");

  if (ypsili.length === 1) {
    const neume = ypsili[0];

    if (
      Math.abs(neume.bounding_circle.x - g.base.bounding_rect.x) <
      Math.abs(
        neume.bounding_circle.x -
          (g.base.bounding_rect.x + g.base.bounding_rect.w)
      )
    ) {
      return QuantitativeNeume.PetastiPlusHypsiliLeft;
    } else {
      return QuantitativeNeume.PetastiPlusHypsiliRight;
    }
  }

  if (ypsili.length === 2) {
    return QuantitativeNeume.PetastiPlusDoubleHypsili;
  }

  if (ypsili.length >= 3) {
    return QuantitativeNeume.PetastiTripleYpsili;
  }

  // Check for petaste used as support
  if (hasAbove(g, "ison")) {
    return QuantitativeNeume.PetastiWithIson;
  }

  if (hasAbove(g, "oligon")) {
    return QuantitativeNeume.PetastiPlusOligon;
  }

  if (hasAbove(g, "yporroe")) {
    return QuantitativeNeume.PetastiPlusHyporoe;
  }

  const hamili = findAbove(g, "hamili");

  if (hamili.length === 1) {
    const apostrofos = has(g, "apostrofos");
    const elafron = has(g, "apostrofos");
    const elafronApostrofos = has(g, "elafron_apostrofos");

    if (apostrofos && !elafron) {
      return QuantitativeNeume.PetastiHamiliApostrofos;
    }

    if (!apostrofos && elafron) {
      return QuantitativeNeume.PetastiHamiliElafron;
    }

    if ((apostrofos && elafron) || elafronApostrofos) {
      return QuantitativeNeume.PetastiHamiliElafronApostrofos;
    }

    return QuantitativeNeume.PetastiHamili;
  }

  if (hamili.length >= 2) {
    if (has(g, "apostrofos")) {
      return QuantitativeNeume.PetastiDoubleHamiliApostrofos;
    }

    return QuantitativeNeume.PetastiDoubleHamili;
  }

  const apostrofosAbove = hasAbove(g, "apostrofos");
  const elafronAbove = hasAbove(g, "elafron");
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos");

  if (apostrofosAbove && !elafronAbove) {
    return QuantitativeNeume.PetastiPlusApostrophos;
  }

  if (!apostrofosAbove && elafronAbove) {
    return QuantitativeNeume.PetastiPlusElaphron;
  }

  if (elafronApostrofosAbove || (elafronAbove && apostrofosAbove)) {
    return QuantitativeNeume.PetastiPlusElaphronPlusApostrophos;
  }

  return QuantitativeNeume.Petasti;
}

function processHamili(g: NeumeGroup) {
  // Check for extra hamili
  const hamili = find(g, "hamli");

  // Handle double hamili
  if (hamili.length === 1) {
    const apostrofos = has(g, "apostrofos");
    const elafron = has(g, "apostrofos");
    const elafronApostrofos = has(g, "elafron_apostrofos");

    if (apostrofos && !elafron) {
      return QuantitativeNeume.DoubleHamiliApostrofos;
    }

    if (!apostrofos && elafron) {
      return QuantitativeNeume.DoubleHamiliElafron;
    }

    if ((apostrofos && elafron) || elafronApostrofos) {
      return QuantitativeNeume.DoubleHamiliElafronApostrofos;
    }

    return QuantitativeNeume.DoubleHamili;
  }

  if (hamili.length >= 2) {
    return QuantitativeNeume.TripleHamili;
  }

  const apostrofosAbove = hasAbove(g, "apostrofos");
  const elafronAbove = hasAbove(g, "elafron");
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos");

  if (apostrofosAbove && !elafronAbove) {
    return QuantitativeNeume.HamiliPlusApostrophos;
  }

  if (!apostrofosAbove && elafronAbove) {
    return QuantitativeNeume.HamiliPlusElaphron;
  }

  if (elafronApostrofosAbove || (elafronAbove && apostrofosAbove)) {
    return QuantitativeNeume.HamiliPlusElaphronPlusApostrophos;
  }

  return QuantitativeNeume.Hamili;
}

function applySanityChecks(
  e: NoteElement,
  g: NeumeGroup,
  segmentation: Segmentation
) {
  const apli = findBelow(g, "apli");
  const klasma = find(g, "klasma");
  const gorgon = find(g, "gorgon");
  const psifiston = findBelow(g, "psifiston");

  const apliConfidence = Math.max(...apli.map((x) => x.confidence));
  const gorgonConfidence = Math.max(...gorgon.map((x) => x.confidence));
  const klasmaConfidence = Math.max(...klasma.map((x) => x.confidence));
  const psifistonConfidence = Math.max(...psifiston.map((x) => x.confidence));

  // Filter out apli that are too low
  for (const a of apli) {
    if (
      a.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h) >=
      segmentation.oligon_height * 2
    ) {
      const index = g.support.indexOf(a);

      if (index !== -1) {
        g.support.splice(index, 1);
      }
    }
  }

  // If there is both a klasma and apli,
  // use the confidence as a tie breaker
  if (apli.length > 0 && klasma.length > 0) {
    if (klasmaConfidence > apliConfidence) {
      g.support = g.support.filter((x) => x.label != "apli");
    } else {
      g.support = g.support.filter((x) => x.label != "klasma");
    }
  }

  // If the group has both a gorgon and klasma,
  // this is probably wrong. So take the highest confidence only.
  if (gorgon.length > 0 && klasma.length > 0) {
    if (klasmaConfidence > gorgonConfidence) {
      g.support = g.support.filter((x) => x.label != "gorgon");
    } else {
      g.support = g.support.filter((x) => x.label != "klasma");
    }
  }

  // If the group has both a gorgon and apli,
  // this is probably wrong. So take the highest confidence only.
  if (gorgon.length > 0 && apli.length > 0) {
    if (apliConfidence > gorgonConfidence) {
      g.support = g.support.filter((x) => x.label != "gorgon");
    } else {
      g.support = g.support.filter((x) => x.label != "apli");
    }
  }

  // If the group has both a gorgon/apli and psifiston,
  // this is probably wrong. So take the highest confidence only.
  if (psifiston.length > 0 && gorgon.length > 0) {
    if (psifistonConfidence > gorgonConfidence) {
      g.support = g.support.filter((x) => x.label != "gorgon");
    } else {
      g.support = g.support.filter((x) => x.label != "psifiston");
    }
  }

  if (psifiston.length > 0 && apli.length > 0) {
    if (psifistonConfidence > apliConfidence) {
      g.support = g.support.filter((x) => x.label != "apli");
    } else {
      g.support = g.support.filter((x) => x.label != "psifiston");
    }
  }
}

function applyAntikenoma(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "antikenoma")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
  } else if (g.support?.find((x) => x.label === "antikenoma_apli")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
    e.timeNeume = TimeNeume.Hapli;
  }
}

function applyGorgon(e: NoteElement, g: NeumeGroup) {
  const gorgon = find(g, "gorgon", 0.5);

  // TODO secondary/tertiary gorgons

  if (gorgon.length > 0) {
    e.gorgonNeume =
      gorgon[0].bounding_circle.y <= g.base.bounding_circle.y
        ? GorgonNeume.Gorgon_Top
        : GorgonNeume.Gorgon_Bottom;
  }
}

function applyDigorgon(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "digorgon");

  // TODO secondary/tertiary gorgons

  if (support) {
    e.gorgonNeume = GorgonNeume.Digorgon;
  }
}

function applyTrigorgon(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "digorgon");

  // TODO secondary/tertiary gorgons

  if (support) {
    e.gorgonNeume = GorgonNeume.Digorgon;
  }
}

function applyKlasma(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "klasma");

  if (support) {
    e.timeNeume =
      support.bounding_circle.y <= g.base.bounding_circle.y
        ? TimeNeume.Klasma_Top
        : TimeNeume.Klasma_Bottom;
  }
}

function applyApli(e: NoteElement, g: NeumeGroup) {
  const apli = findBelow(g, "apli");

  if (apli.length == 1) {
    e.timeNeume = TimeNeume.Hapli;
  } else if (apli.length == 2) {
    e.timeNeume = TimeNeume.Dipli;
  } else if (apli.length == 3) {
    e.timeNeume = TimeNeume.Tripli;
  } else if (apli.length >= 4) {
    e.timeNeume = TimeNeume.Tetrapli;
  }
}

function applyFthora(e: NoteElement, g: NeumeGroup) {
  const fthora = g.support?.find((x) => x.label.startsWith("fthora"));

  // TODO secondary/tertiary gorgons

  if (fthora) {
    if (fthora.bounding_rect.y < g.base.bounding_rect.y) {
      if (fthora.label === "fthora_diatonic_di") {
        e.fthora = Fthora.DiatonicThi_Top;
      } else if (fthora.label === "fthora_diatonic_ke") {
        e.fthora = Fthora.DiatonicKe_Top;
      } else if (fthora.label === "fthora_diatonic_pa") {
        e.fthora = Fthora.DiatonicPa_Top;
      } else if (fthora.label === "fthora_enharmonic") {
        e.fthora = Fthora.Enharmonic_Top;
      } else if (fthora.label === "fthora_hard_chromatic_di") {
        e.fthora = Fthora.HardChromaticThi_Top;
      } else if (fthora.label === "fthora_hard_chromatic_pa") {
        e.fthora = Fthora.HardChromaticPa_Top;
      } else if (fthora.label === "fthora_soft_chromatic_di") {
        e.fthora = Fthora.SoftChromaticThi_Top;
      }
    } else {
      if (fthora.label === "fthora_diatonic_di") {
        e.fthora = Fthora.DiatonicThi_Bottom;
      } else if (fthora.label === "fthora_diatonic_ke") {
        e.fthora = Fthora.DiatonicKe_Bottom;
      } else if (fthora.label === "fthora_diatonic_pa") {
        e.fthora = Fthora.DiatonicPa_Bottom;
      } else if (fthora.label === "fthora_enharmonic") {
        e.fthora = Fthora.Enharmonic_Bottom;
      } else if (fthora.label === "fthora_hard_chromatic_di") {
        e.fthora = Fthora.HardChromaticThi_Bottom;
      } else if (fthora.label === "fthora_hard_chromatic_pa") {
        e.fthora = Fthora.HardChromaticPa_Bottom;
      } else if (fthora.label === "fthora_soft_chromatic_di") {
        e.fthora = Fthora.SoftChromaticThi_Bottom;
      }
    }
  }
}

function applyPsifiston(e: NoteElement, g: NeumeGroup) {
  if (hasBelow(g, "psifiston", 0.75)) {
    e.vocalExpressionNeume = VocalExpressionNeume.Psifiston;
  }
}

function applyHeteron(e: NoteElement, g: NeumeGroup) {
  const heteron = findBelow(g, "heteron", 0);
  if (heteron.length > 0) {
    if (heteron[0].bounding_rect.x > g.base.bounding_rect.x) {
      // TODO figure out if it's connecting or not
      // Probably need to be able to detect apli before we can do this.
      e.vocalExpressionNeume = VocalExpressionNeume.HeteronConnecting;
    }
  }
}

function applyHomalon(e: NoteElement, g: NeumeGroup) {
  const homalon = findBelow(g, "omalon", 0);
  if (homalon.length > 0) {
    if (homalon[0].bounding_rect.x > g.base.bounding_rect.x) {
      if (hasAbove(g, "klasma")) {
        e.vocalExpressionNeume = VocalExpressionNeume.Homalon;
      } else {
        e.vocalExpressionNeume = VocalExpressionNeume.HomalonConnecting;
      }
    }
  }
}

function applyEndofonon(e: NoteElement, g: NeumeGroup) {
  const endofonon = findBelow(g, "endofonon", 0);
  if (endofonon.length > 0) {
    if (endofonon[0].bounding_rect.x > g.base.bounding_rect.x) {
      e.vocalExpressionNeume = VocalExpressionNeume.Endofonon;
    }
  }
}

function applyStavros(e: NoteElement, g: NeumeGroup) {
  const stavros = has(g, "stavros", 0);
  if (stavros) {
    e.vocalExpressionNeume = VocalExpressionNeume.Cross_Top;
  }
}

function is_base(neume: string) {
  return [
    "ison",
    "oligon",
    "petaste",
    "apostrofos",
    "elafron",
    "elafron_apostrofos",
    "vareia",
    "kentima",
    "yporroe",
  ].includes(neume);
}

function touches_baseline(match: ContourMatch, baseline: number) {
  return (
    match.bounding_rect.y <= baseline &&
    baseline <= match.bounding_rect.y + match.bounding_rect.h
  );
}

function centerOverlaps(
  base: AugmentedContourMatch,
  support: AugmentedContourMatch
) {
  return (
    base.bounding_rect.x <= support.bounding_circle.x &&
    support.bounding_circle.x <= base.bounding_rect.x + base.bounding_rect.w
  );
}

function overlaps(
  base: ContourMatch,
  support: ContourMatch,
  threshold: number
) {
  const left = Math.max(base.bounding_rect.x, support.bounding_rect.x);
  const right = Math.min(
    base.bounding_rect.x + base.bounding_rect.w,
    support.bounding_rect.x + support.bounding_rect.w
  );

  return (right - left) / support.bounding_rect.w >= threshold;
}

function findAbove(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.bounding_rect.y < g.base.bounding_rect.y &&
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}

function findBelow(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.bounding_rect.y > g.base.bounding_rect.y &&
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}
function find(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}

function hasAbove(g: NeumeGroup, label: string, threshold = 1) {
  return findAbove(g, label, threshold).length > 0;
}

function hasBelow(g: NeumeGroup, label: string, threshold = 1) {
  return findBelow(g, label, threshold).length > 0;
}

function has(g: NeumeGroup, label: string, threshold = 1) {
  return find(g, label, threshold).length > 0;
}

function groupMatches(
  analysis: PageAnalysis,
  confidence_threshold = 0,
  martyria_confidence_threshold = 0
) {
  const groups: NeumeGroup[] = [];

  // Filter out bad matches and convert the remaining matches
  // into our augmented data model
  const matches = analysis.matches
    .filter(
      (x) =>
        x.line >= 0 && x.label != null && x.confidence > confidence_threshold
    )
    .map((x) => new AugmentedContourMatch(x));

  // Form groups. There are two types of groups:
  // 1) Base neumes that touch the baseline
  // 2) Martyria
  // TODO Chronos groups and others (?)
  for (const [i, m] of matches.entries()) {
    m.isBase =
      is_base(m.label) &&
      touches_baseline(m, analysis.segmentation.baselines[m.line]);

    const isMartyria =
      m.label.startsWith("martyria") &&
      !m.label.startsWith("martyria_root") &&
      m.confidence > martyria_confidence_threshold;

    if (m.isBase || isMartyria) {
      const g = new NeumeGroup();
      groups.push(g);
      g.base = m;

      // Find the supporting neumes to the right
      for (let j = i + 1; j < matches.length; j++) {
        const s = matches[j];

        // Stop if we are not on the same line number
        if (s.line != m.line) {
          break;
        }

        // Stop if the neumes are too far to the right.
        // That is, the left edge is farther right than the right edge
        // of the base neume
        if (s.bounding_rect.x > m.bounding_rect.x + m.bounding_rect.w) {
          break;
        }

        g.support.push(s);
      }

      // Find the supporting neumes to the left
      for (let j = i - 1; j >= 0; j--) {
        const s = matches[j];

        // Stop if we are not on the same line number
        if (s.line != m.line) {
          break;
        }

        // Stop if the neumes are too far to the right.
        // That is, the right edge is farther left than the left edge
        // of the base neume
        if (s.bounding_rect.x + s.bounding_rect.w < m.bounding_rect.x) {
          break;
        }

        // Ignore other base neumes
        if (s.isBase) {
          continue;
        }

        g.support.push(s);
      }
    }
  }

  return groups;
}

function processAnalysis(
  analysis: OcrAnalysis,
  confidence_threshold = 0,
  martyria_confidence_threshold = 0
) {
  const elements: ScoreElement[] = [];

  for (let page of analysis.pages) {
    for (let e of processPageAnalysis(
      page,
      confidence_threshold,
      martyria_confidence_threshold
    )) {
      elements.push(e);
    }
  }

  return elements;
}

function processPageAnalysis(
  analysis: PageAnalysis,
  confidence_threshold = 0,
  martyria_confidence_threshold = 0
) {
  const elements: ScoreElement[] = [];

  const groups = groupMatches(
    analysis,
    confidence_threshold,
    martyria_confidence_threshold
  );

  // const test_group = groups[173];
  // console.log(test_group);
  // console.log(processOligon(test_group));
  // console.log(has(test_group, "ypsili"));

  let vareia = false;

  for (let i = 0; i < groups.length; i++) {
    const g = groups[i];

    let prev: NeumeGroup | null = null;
    let next: NeumeGroup | null = null;
    let nextNext: NeumeGroup | null = null;

    if (i - 1 >= 0) {
      prev = groups[i - 1];
    }

    if (i + 1 < groups.length) {
      next = groups[i + 1];
    }

    if (i + 2 < groups.length) {
      nextNext = groups[i + 2];
    }

    if (g.base.isBase) {
      const e = new NoteElement();

      if (g.base.label === "oligon") {
        if (
          next?.base.line === g.base.line &&
          next?.base.label === "kentima" &&
          (nextNext?.base.label !== "kentima" ||
            nextNext?.base.line !== g.base.line)
        ) {
          // Combine the kentima with the oligon and skip ahead
          g.support.push(...next.support);
          i++;
          e.quantitativeNeume = processOligonWithMiddleKentima(g);
        } else {
          e.quantitativeNeume = processOligon(g);
        }
      } else if (g.base.label === "ison") {
        e.quantitativeNeume = processIson(g);
      } else if (g.base.label === "petaste") {
        e.quantitativeNeume = processPetaste(g);
      } else if (g.base.label === "apostrofos") {
        e.quantitativeNeume = processApostrofos(g);

        if (
          e.quantitativeNeume === QuantitativeNeume.Apostrophos &&
          next?.base.line === g.base.line &&
          next?.base.label === "elafron"
        ) {
          // Combine the apostrofos with the elafron
          e.quantitativeNeume = QuantitativeNeume.RunningElaphron;
          g.support.push(...next.support);
          i++;
        } else if (
          e.quantitativeNeume === QuantitativeNeume.Apostrophos &&
          next?.base.line === g.base.line &&
          next?.base.label === "petaste" &&
          hasAbove(next, "elafron")
        ) {
          // Combine the apostrofos with the petasti+elafron
          e.quantitativeNeume = QuantitativeNeume.PetastiPlusRunningElaphron;
          g.support.push(...next.support);
          i++;
        }
      } else if (g.base.label === "yporroe") {
        e.quantitativeNeume = QuantitativeNeume.Hyporoe;
      } else if (g.base.label === "elafron") {
        e.quantitativeNeume = QuantitativeNeume.Elaphron;

        const apostrofos = find(g, "apostrofos");

        if (apostrofos.length > 0) {
          e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

          // Sometimes the apostrofos is double detected
          if (next?.base === apostrofos[0]) {
            g.support.push(...next.support);
            i++;
          }
        }
      } else if (g.base.label === "elafron_apostrofos") {
        e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

        const apostrofos = find(g, "apostrofos");

        // Sometimes the apostrofos is double detected
        if (apostrofos.length > 0) {
          if (next?.base === apostrofos[0]) {
            g.support.push(...next.support);
            i++;
          }
        }
      } else if (g.base.label === "hamili") {
        e.quantitativeNeume = processHamili(g);
      } else if (g.base.label === "kentima") {
        if (next?.base.line === g.base.line && next?.base.label === "kentima") {
          e.quantitativeNeume = QuantitativeNeume.Kentemata;
          g.support.push(...next.support);
          i++;
        }
      } else if (g.base.label === "vareia") {
        vareia = true;
        applyGorgon(e, g);
        // TODO process apli
        continue;
      } else if (g.base.label === "stavros") {
        e.quantitativeNeume = QuantitativeNeume.Cross;
      }

      applySanityChecks(e, g, analysis.segmentation);

      applyAntikenoma(e, g);
      applyGorgon(e, g);
      applyDigorgon(e, g);
      applyTrigorgon(e, g);
      applyApli(e, g);
      applyKlasma(e, g);
      applyFthora(e, g);
      applyPsifiston(e, g);
      applyHeteron(e, g);
      applyHomalon(e, g);
      applyEndofonon(e, g);
      applyStavros(e, g);

      if (vareia) {
        e.vareia = true;
        vareia = false;
      }

      elements.push(e);
    } else if (
      g.base.label.startsWith("martyria") &&
      !g.base.label.startsWith("martyria_root")
    ) {
      // TODO make this smarter
      const e = new MartyriaElement();
      e.auto = true;
      elements.push(e);

      // If the martyria is more than 2 * oligon_width away from the previous neume,
      // we assume it is a right aligned martyria
      if (
        prev != null &&
        g.base.line === prev.base.line &&
        g.base.bounding_rect.x -
          (prev.base.bounding_rect.x + prev.base.bounding_rect.w) >=
          analysis.segmentation.oligon_width * 2
      ) {
        e.alignRight = true;
      }
    }
  }

  return elements;
}
