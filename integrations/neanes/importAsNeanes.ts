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

const elements = processAnalysis(analysis, 0, 0.9);

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

function process_ison(e, g) {
  if (has_support(g, ["apostrofos"])) {
    e.quantitativeNeume = QuantitativeNeume.IsonPlusApostrophos;
  } else {
    e.quantitativeNeume = QuantitativeNeume.Ison;
  }
}

function process_oligon(g: NeumeGroup) {
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

function process_oligon_with_middle_kentima(g: NeumeGroup) {
  // Check kentima above
  const kentimaAbove = hasAbove(g, "kentima");

  // Handle oligon + kentemata
  if (kentimaAbove.length >= 2) {
    return QuantitativeNeume.OligonKentimaMiddleKentimata;
  }

  return QuantitativeNeume.OligonPlusKentima;
}

function process_petaste(e: NoteElement, g: NeumeGroup) {
  e.quantitativeNeume = QuantitativeNeume.Petasti;

  if (has_support(g, ["kentima"])) {
    e.quantitativeNeume = QuantitativeNeume.PetastiPlusKentimaAbove;
  } else if (has_support(g, ["apostrofos"])) {
    e.quantitativeNeume = QuantitativeNeume.PetastiPlusApostrophos;
  }
}

function process_antikenoma(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "antikenoma")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
  } else if (g.support?.find((x) => x.label === "antikenoma_apli")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
    e.timeNeume = TimeNeume.Hapli;
  }
}

function process_gorgon(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "gorgon");

  if (support) {
    e.gorgonNeume =
      support.bounding_circle.y <= g.base.bounding_circle.y
        ? GorgonNeume.Gorgon_Top
        : GorgonNeume.Gorgon_Bottom;
  }
}

function process_digorgon(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "digorgon");

  if (support) {
    e.gorgonNeume = GorgonNeume.Digorgon;
  }
}

function process_kentima(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.filter((x) => x.label === "kentima");

  if (support?.length === 2) {
    if (e.quantitativeNeume === "Oligon") {
      e.quantitativeNeume =
        support[0].bounding_circle.y <= g.base.bounding_circle.y
          ? QuantitativeNeume.OligonPlusKentemata
          : QuantitativeNeume.KentemataPlusOligon;
    }
  } else if (support?.length === 1) {
    if (e.quantitativeNeume === "Oligon") {
      e.quantitativeNeume =
        support[0].bounding_circle.y <= g.base.bounding_circle.y
          ? QuantitativeNeume.OligonPlusKentimaAbove
          : QuantitativeNeume.OligonPlusKentimaBelow;
    }
  }
}

function process_klasma(e: NoteElement, g: NeumeGroup) {
  const support = g.support?.find((x) => x.label === "klasma");

  if (support) {
    e.timeNeume =
      support.bounding_circle.y <= g.base.bounding_circle.y
        ? TimeNeume.Klasma_Top
        : TimeNeume.Klasma_Bottom;
  }
}

function process_psifiston(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "psifiston")) {
    e.vocalExpressionNeume = VocalExpressionNeume.Psifiston;
  }
}

function process_syndesmos(e: NoteElement, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "syndesmos")) {
    // TODO use position to decide if it's connecting
    e.vocalExpressionNeume = VocalExpressionNeume.HeteronConnecting;
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

function above_baseline(match: ContourMatch, baseline: number) {
  return match.bounding_rect.y + match.bounding_rect.h <= baseline;
}

function below_baseline(match: ContourMatch, baseline: number) {
  return match.bounding_rect.y >= baseline;
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

// function processAnalysisOld() {
//   const groups = groupMatches(analysis, 0, 0.95);

//   let vareia = false;

//   for (let i = 0; i < groups.length; i++) {
//     const g = groups[i];

//     let next: NeumeGroup | null = null;
//     let nextNext: NeumeGroup | null = null;

//     if (i + 1 < groups.length) {
//       next = groups[i + 1];
//     }

//     if (i + 2 < groups.length) {
//       nextNext = groups[i + 2];
//     }

//     if (g.base.label.startsWith("martyria")) {
//       const e = new MartyriaElement();
//       e.auto = true;
//       score.staff.elements.push(e);
//       continue;
//     }

//     const e = new NoteElement();

//     if (g.base.label === "ison") {
//       process_ison(e, g);
//     } else if (g.base.label === "petaste") {
//       process_petaste(e, g);
//     } else if (g.base.label === "oligon") {
//       process_oligon(e, g);

//       if (
//         next?.base.label === "kentima" &&
//         nextNext?.base.label !== "kentima"
//       ) {
//         e.quantitativeNeume = QuantitativeNeume.OligonPlusKentima;

//         if (has_support(g, ["kentima"])) {
//           e.quantitativeNeume = QuantitativeNeume.OligonKentimaMiddleKentimata;
//         }

//         g.support.push(...next.support);
//         i++;
//       }
//     } else if (g.base.label === "apostrofos") {
//       e.quantitativeNeume = QuantitativeNeume.Apostrophos;
//     } else if (g.base.label === "yporroe") {
//       e.quantitativeNeume = QuantitativeNeume.Hyporoe;
//     } else if (g.base.label === "elafron") {
//       e.quantitativeNeume = QuantitativeNeume.Elaphron;

//       if (has_support(g, ["apostrofos"])) {
//         e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;
//       }
//     } else if (g.base.label === "elafron_apostrofos") {
//       e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;
//     } else if (g.base.label === "kentima") {
//       if (next?.base.label === "kentima") {
//         e.quantitativeNeume = QuantitativeNeume.Kentemata;
//         g.support.push(...next.support);
//         i++;
//       }
//     } else if (g.base.label === "vareia") {
//       vareia = true;
//       process_gorgon(e, g);
//       // TODO process apli
//       continue;
//     }

//     process_antikenoma(e, g);
//     process_gorgon(e, g);
//     process_digorgon(e, g);
//     process_kentima(e, g);
//     process_klasma(e, g);
//     process_psifiston(e, g);
//     process_syndesmos(e, g);

//     if (vareia) {
//       e.vareia = true;
//       vareia = false;
//     }

//     score.staff.elements.push(e);
//   }
// }

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

  const test_group = groups[19];
  console.log(test_group);
  console.log(process_oligon_with_middle_kentima(test_group));
  console.log(hasAbove(test_group, "kentima"));

  let vareia = false;

  for (let i = 0; i < groups.length; i++) {
    const g = groups[i];

    let next: NeumeGroup | null = null;
    let nextNext: NeumeGroup | null = null;

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
          next?.base.label === "kentima" &&
          nextNext?.base.label !== "kentima"
        ) {
          // Combine the kentima with the oligon and skip ahead
          g.support.push(...next.support);
          i++;
          e.quantitativeNeume = process_oligon_with_middle_kentima(g);
        } else {
          e.quantitativeNeume = process_oligon(g);
        }
      } else if (g.base.label === "ison") {
        process_ison(e, g);
      } else if (g.base.label === "petaste") {
        process_petaste(e, g);
      } else if (g.base.label === "apostrofos") {
        e.quantitativeNeume = QuantitativeNeume.Apostrophos;
      } else if (g.base.label === "yporroe") {
        e.quantitativeNeume = QuantitativeNeume.Hyporoe;
      } else if (g.base.label === "elafron") {
        e.quantitativeNeume = QuantitativeNeume.Elaphron;

        if (has_support(g, ["apostrofos"])) {
          e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;
        }
      } else if (g.base.label === "elafron_apostrofos") {
        e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;
      } else if (g.base.label === "kentima") {
        if (next?.base.label === "kentima") {
          e.quantitativeNeume = QuantitativeNeume.Kentemata;
          g.support.push(...next.support);
          i++;
        }
      } else if (g.base.label === "vareia") {
        vareia = true;
        process_gorgon(e, g);
        // TODO process apli
        continue;
      }

      process_antikenoma(e, g);
      process_gorgon(e, g);
      process_digorgon(e, g);
      process_klasma(e, g);
      process_psifiston(e, g);
      process_syndesmos(e, g);

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
    }
  }

  return elements;
}
