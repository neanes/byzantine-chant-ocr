import { promises as fs } from "fs";
import YAML from "yaml";
import { Score } from "./neanes/models/Score";
import { EmptyElement, NoteElement } from "./neanes/models/Element";
import {
  GorgonNeume,
  Neume,
  QuantitativeNeume,
  TimeNeume,
  VocalExpressionNeume,
} from "./neanes/models/Neumes";
import { AugmentedContourMatch, NeumeGroup } from "./OcrImportCustomModels";
import { ContourMatch, OcrAnalysis } from "./OcrAnalysis";
import { SaveService } from "./neanes/services/SaveService";

// Blank score
const score = new Score();
const analysis: OcrAnalysis = YAML.parse(
  await fs.readFile("output.yaml", "utf8")
);

// Remove the empty element
score.staff.elements.pop();

const groups = groupMatches(analysis);

let vareia = false;

for (let i = 0; i < groups.length; i++) {
  const g = groups[i];

  let next: NeumeGroup | null = null;

  if (i + 1 < groups.length) {
    next = groups[i + 1];
  }

  const e = new NoteElement();

  if (g.base.label === "ison") {
    process_ison(e, g);
  } else if (g.base.label === "petaste") {
    e.quantitativeNeume = QuantitativeNeume.Petasti;
  } else if (g.base.label === "oligon") {
    process_oligon(e, g);

    if (next?.base.label === "kentima") {
      e.quantitativeNeume = QuantitativeNeume.OligonPlusKentima;

      if (has_support(g, ["kentima"])) {
        e.quantitativeNeume = QuantitativeNeume.OligonKentimaMiddleKentimata;
      }

      g.support.push(...next.support);
      i++;
    }
  } else if (g.base.label === "apostrofos") {
    e.quantitativeNeume = QuantitativeNeume.Apostrophos;
  } else if (g.base.label === "yporroe") {
    e.quantitativeNeume = QuantitativeNeume.Hyporoe;
  } else if (g.base.label === "elafron") {
    e.quantitativeNeume = QuantitativeNeume.Elaphron;

    if (g.support?.find((x) => x.label === "apostrofos")) {
      e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;
    }
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
  process_kentima(e, g);
  process_klasma(e, g);
  process_psifiston(e, g);
  process_syndesmos(e, g);

  if (vareia) {
    e.vareia = true;
    vareia = false;
  }

  score.staff.elements.push(e);
}

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

function process_oligon(e: NoteElement, g: NeumeGroup) {
  if (has_support(g, ["ison", "kentima"])) {
    e.quantitativeNeume = QuantitativeNeume.OligonPlusIsonPlusKentemata;
  } else if (has_support(g, ["apostrofos", "kentima"])) {
    e.quantitativeNeume = QuantitativeNeume.OligonPlusApostrophosPlusKentemata;
  } else if (has_support(g, ["elafron", "apostrofos", "kentima"])) {
    e.quantitativeNeume =
      QuantitativeNeume.OligonPlusElaphronPlusApostrophosPlusKentemata;
  } else if (has_support(g, ["elafron", "kentima"])) {
    e.quantitativeNeume = QuantitativeNeume.OligonPlusElaphronPlusKentemata;
  } else {
    e.quantitativeNeume = QuantitativeNeume.Oligon;
  }
}

function process_antikenoma(e, g: NeumeGroup) {
  if (g.support?.find((x) => x.label === "antikenoma")) {
    e.vocalExpressionNeume = "Antikenoma";
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

function groupMatches(analysis: OcrAnalysis, confidence_threshold = 0) {
  const groups: NeumeGroup[] = [];

  const matches = analysis.matches
    .filter(
      (x) =>
        x.line >= 0 && x.label != null && x.confidence > +confidence_threshold
    )
    .map((x) => new AugmentedContourMatch(x));

  for (const m of matches) {
    m.isBase =
      is_base(m.label) &&
      touches_baseline(m, analysis.segmentation.baselines[m.line]);

    if (m.isBase) {
      const g = new NeumeGroup();
      g.base = m;

      // Find the supporting neumes
      for (const s of matches) {
        // Skip neumes that are too high or that have a low confidence
        // Also skip neumes that were already classified as a base.
        if (
          s.line < m.line ||
          s.label == null ||
          s.confidence < confidence_threshold ||
          s.isBase ||
          s.isGrouped
        ) {
          continue;
        }

        // Stop if we have reached neumes that are too low
        if (s.line > m.line) {
          break;
        }

        // Skip if the neume is too far to the left or the right
        if (
          s.bounding_rect.x + s.bounding_rect.w <= m.bounding_rect.x ||
          s.bounding_rect.x >= m.bounding_rect.x + m.bounding_rect.w
        ) {
          continue;
        }

        if (overlaps(m, s, 0.6)) {
          g.support.push(s);
          s.isGrouped = true;
        }
      }
      groups.push(g);
    }
  }

  return groups;
}
