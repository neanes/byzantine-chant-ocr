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
import { ContourMatch, OcrAnalysis } from "./OcrAnalysis";
import { SaveService } from "./neanes/services/SaveService";

// Blank score
const score = new Score();
const analysis: OcrAnalysis = YAML.parse(
  await fs.readFile("output.yaml", "utf8")
);

const min_confidence_threshold = 0.7;

const elements = processAnalysis(analysis, min_confidence_threshold, 0.9);

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
  if (has(g, "apostrofos").length) {
    return QuantitativeNeume.IsonPlusApostrophos;
  }
  return QuantitativeNeume.Ison;
}

function processApostrofos(g: NeumeGroup) {
  if (has(g, "apostrofos").length) {
    return QuantitativeNeume.DoubleApostrophos;
  }

  return QuantitativeNeume.Apostrophos;
}

function processOligon(g: NeumeGroup) {
  // Check kentima below
  const kentimaBelow = hasBelow(g, "kentima");

  if (kentimaBelow.length === 1) {
    return QuantitativeNeume.OligonPlusKentimaBelow;
  }

  if (kentimaBelow.length >= 2) {
    return QuantitativeNeume.KentemataPlusOligon;
  }

  // Check kentima above
  const kentimaAbove = hasAbove(g, "kentima");

  // Handle oligon + kentemata
  if (kentimaAbove.length >= 2) {
    if (hasAbove(g, "ison").length) {
      return QuantitativeNeume.OligonPlusIsonPlusKentemata;
    }

    const apostrofosAbove = hasAbove(g, "apostrofos");
    const elafronAbove = hasAbove(g, "elafron");
    const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos").length > 0;

    if (apostrofosAbove.length && !elafronAbove.length) {
      return QuantitativeNeume.OligonPlusApostrophosPlusKentemata;
    }

    if (!apostrofosAbove.length && elafronAbove.length) {
      return QuantitativeNeume.OligonPlusElaphronPlusKentemata;
    }

    if (elafronApostrofosAbove) {
      return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata;
    }

    // Sometimes OCR detects elafron_apostrofos as one character,
    // sometimes as two. So this may be a running elafron.
    if (apostrofosAbove.length && elafronAbove.length) {
      if (
        apostrofosAbove[0].bounding_rect.x < elafronAbove[0].bounding_rect.x
      ) {
        return QuantitativeNeume.OligonPlusRunningElaphronPlusKentemata;
      }
      return QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata;
    }

    if (hasAbove(g, "yporroe").length) {
      return QuantitativeNeume.OligonPlusHyporoePlusKentemata;
    }

    if (hasAbove(g, "hamili").length) {
      return QuantitativeNeume.OligonPlusHamiliPlusKentemata;
    }

    const ypsili = hasAbove(g, "ypsili");

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
    const ypsili = hasAbove(g, "ypsili");

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
  const ypsili = hasAbove(g, "ypsili");

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
  if (hasAbove(g, "ison").length) {
    return QuantitativeNeume.OligonPlusIson;
  }

  if (hasAbove(g, "apostrofos").length) {
    return QuantitativeNeume.OligonPlusApostrophos;
  }

  if (hasAbove(g, "yporroe").length) {
    return QuantitativeNeume.OligonPlusHyporoe;
  }

  const apostrofosAbove = hasAbove(g, "apostrofos").length > 0;
  const elafronAbove = hasAbove(g, "elafron").length > 0;
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos").length > 0;

  if (apostrofosAbove && !elafronAbove) {
    return QuantitativeNeume.OligonPlusApostrophos;
  }

  if (!apostrofosAbove && elafronAbove) {
    return QuantitativeNeume.OligonPlusElaphron;
  }

  if (elafronApostrofosAbove || (elafronAbove && apostrofosAbove)) {
    return QuantitativeNeume.OligonPlusElaphronPlusApostrophos;
  }

  if (hasAbove(g, "hamili").length) {
    return QuantitativeNeume.OligonPlusHamili;
  }

  return QuantitativeNeume.Oligon;
}

function processOligonWithMiddleKentima(g: NeumeGroup) {
  // Check kentima above
  const kentimaAbove = hasAbove(g, "kentima");

  // Handle oligon + kentemata
  if (kentimaAbove.length >= 2) {
    return QuantitativeNeume.OligonKentimaMiddleKentimata;
  }

  return QuantitativeNeume.OligonPlusKentima;
}

function processPetaste(g: NeumeGroup) {
  // Check kentima above
  const kentimaAbove = hasAbove(g, "kentima");

  // Handle petaste + ypsili + kentemata
  if (kentimaAbove.length >= 2) {
    const ypsili = hasAbove(g, "ypsili");

    if (ypsili.length === 2) {
      return QuantitativeNeume.PetastiKentimataDoubleYpsili;
    }

    if (ypsili.length >= 3) {
      return QuantitativeNeume.PetastiKentimataTripleYpsili;
    }
  }

  // Handle petaste with single kentima
  if (kentimaAbove.length == 1) {
    const ypsili = hasAbove(g, "ypsili");

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
  const ypsili = hasAbove(g, "ypsili");

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
  if (hasAbove(g, "ison").length) {
    return QuantitativeNeume.PetastiWithIson;
  }

  if (hasAbove(g, "oligon").length) {
    return QuantitativeNeume.PetastiPlusOligon;
  }

  if (hasAbove(g, "yporroe").length) {
    return QuantitativeNeume.PetastiPlusHyporoe;
  }

  const hamili = hasAbove(g, "hamili");

  if (hamili.length === 1) {
    const apostrofos = has(g, "apostrofos").length > 0;
    const elafron = has(g, "apostrofos").length > 0;
    const elafronApostrofos = has(g, "elafron_apostrofos").length > 0;

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
    if (has(g, "apostrofos").length) {
      return QuantitativeNeume.PetastiDoubleHamiliApostrofos;
    }

    return QuantitativeNeume.PetastiDoubleHamili;
  }

  const apostrofosAbove = hasAbove(g, "apostrofos").length > 0;
  const elafronAbove = hasAbove(g, "elafron").length > 0;
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos").length > 0;

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
  const hamili = has(g, "hamli");

  // Handle double hamili
  if (hamili.length === 1) {
    const apostrofos = has(g, "apostrofos").length > 0;
    const elafron = has(g, "apostrofos").length > 0;
    const elafronApostrofos = has(g, "elafron_apostrofos").length > 0;

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

  const apostrofosAbove = hasAbove(g, "apostrofos").length > 0;
  const elafronAbove = hasAbove(g, "elafron").length > 0;
  const elafronApostrofosAbove = hasAbove(g, "elafron_apostrofos").length > 0;

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

function applyAntikenoma(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "antikenoma")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
  } else if (g.support?.find((x) => x.label === "antikenoma_apli")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
    e.timeNeume = TimeNeume.Hapli;
  }
}

function applyGorgon(e: NoteElement, g: NeumeGroup) {
  const gorgon = has(g, "gorgon", 0.5);

  // TODO secondary/tertiary gorgons

  if (gorgon.length) {
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
      }
    }
  }
}

function applyPsifiston(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "psifiston")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Psifiston;
  }
}

function applyHeteron(e: NoteElement, g: NeumeGroup) {
  const heteron = hasBelow(g, "heteron", 0);
  if (heteron.length) {
    if (heteron[0].bounding_rect.x > g.base.bounding_rect.x) {
      // TODO figure out if it's connecting or not
      // Probably need to be able to detect apli before we can do this.
      e.vocalExpressionNeume = VocalExpressionNeume.HeteronConnecting;
    }
  }
}

function applyHomalon(e: NoteElement, g: NeumeGroup) {
  const heteron = hasBelow(g, "omalon", 0);
  if (heteron.length) {
    if (heteron[0].bounding_rect.x > g.base.bounding_rect.x) {
      if (hasAbove(g, "klasma").length) {
        e.vocalExpressionNeume = VocalExpressionNeume.Homalon;
      } else {
        e.vocalExpressionNeume = VocalExpressionNeume.HomalonConnecting;
      }
    }
  }
}

function applyEndofonon(e: NoteElement, g: NeumeGroup) {
  const endofonon = hasBelow(g, "endofonon", 0);
  if (endofonon.length) {
    if (endofonon[0].bounding_rect.x > g.base.bounding_rect.x) {
      e.vocalExpressionNeume = VocalExpressionNeume.Endofonon;
    }
  }
}

function applyStavros(e: NoteElement, g: NeumeGroup) {
  const stavros = has(g, "stavros", 0);
  if (stavros.length) {
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

function hasAbove(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.bounding_rect.y < g.base.bounding_rect.y &&
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}

function hasBelow(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.bounding_rect.y > g.base.bounding_rect.y &&
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}
function has(g: NeumeGroup, label: string, threshold = 1) {
  return g.support.filter(
    (x) =>
      x.label === label &&
      (centerOverlaps(g.base, x) || overlaps(g.base, x, threshold))
  );
}

function groupMatches(
  analysis: OcrAnalysis,
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

      // Find the supporting neumes to the right
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

  const groups = groupMatches(
    analysis,
    confidence_threshold,
    martyria_confidence_threshold
  );

  // const test_group = groups[0];
  // console.log(test_group);
  // console.log(processApostrofos(test_group));
  // console.log(has(test_group, "apostrofos"));

  let vareia = false;

  let temp = 0;

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
          hasAbove(next, "elafron").length
        ) {
          console.log(next);
          // Combine the apostrofos with the petasti+elafron
          e.quantitativeNeume = QuantitativeNeume.PetastiPlusRunningElaphron;
          g.support.push(...next.support);
          i++;
        }
      } else if (g.base.label === "yporroe") {
        e.quantitativeNeume = QuantitativeNeume.Hyporoe;
      } else if (g.base.label === "elafron") {
        e.quantitativeNeume = QuantitativeNeume.Elaphron;

        const apostrofos = has(g, "apostrofos");

        if (apostrofos.length) {
          e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

          // Sometimes the apostrofos is double detected
          if (next?.base === apostrofos[0]) {
            g.support.push(...next.support);
            i++;
          }
        }
      } else if (g.base.label === "elafron_apostrofos") {
        e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

        const apostrofos = has(g, "apostrofos");

        // Sometimes the apostrofos is double detected
        if (apostrofos.length) {
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

      applyAntikenoma(e, g);
      applyGorgon(e, g);
      applyDigorgon(e, g);
      applyTrigorgon(e, g);
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
    } else if (g.base.label.startsWith("martyria")) {
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
      } else {
        if (temp === 3) {
          console.log(analysis.segmentation.oligon_width);
        }
        temp++;
      }
    }
  }

  return elements;
}
