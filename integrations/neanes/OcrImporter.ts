import YAML from 'yaml';
import {
  LineBreakType,
  MartyriaElement,
  NoteElement,
  ScoreElement,
  TempoElement,
} from './neanes/models/Element';
import {
  Fthora,
  GorgonNeume,
  QuantitativeNeume,
  TempoSign,
  TimeNeume,
  VocalExpressionNeume,
} from './neanes/models/Neumes';
import { AugmentedContourMatch, NeumeGroup } from './OcrImportCustomModels';
import {
  ContourMatch,
  OcrAnalysis,
  PageAnalysis,
  Segmentation,
} from './OcrAnalysis';

export class OcrImporterOptions {
  min_confidence_threshold: number = 0.7;
  martyria_confidence_threshold: number = 0.8;
}

export class OcrImporter {
  public import(data: string, options?: OcrImporterOptions) {
    const analysis: OcrAnalysis = YAML.parse(data);

    const elements = this.processAnalysis(
      analysis,
      options ?? new OcrImporterOptions(),
    );

    return elements;
  }

  processIson(g: NeumeGroup) {
    if (this.has(g, 'apostrofos')) {
      return QuantitativeNeume.IsonPlusApostrophos;
    }
    return QuantitativeNeume.Ison;
  }

  processApostrofos(g: NeumeGroup) {
    if (this.has(g, 'apostrofos')) {
      return QuantitativeNeume.DoubleApostrophos;
    }

    return QuantitativeNeume.Apostrophos;
  }

  processOligon(g: NeumeGroup) {
    // Check kentima below
    const kentimaBelow = this.findBelow(g, 'kentima');

    if (kentimaBelow.length === 1) {
      return QuantitativeNeume.OligonPlusKentimaBelow;
    }

    if (kentimaBelow.length >= 2) {
      return QuantitativeNeume.KentemataPlusOligon;
    }

    // Check kentima above
    const kentimaAbove = this.findAbove(g, 'kentima');

    // Handle oligon + kentemata
    if (kentimaAbove.length >= 2) {
      if (this.hasAbove(g, 'ison')) {
        return QuantitativeNeume.OligonPlusIsonPlusKentemata;
      }

      const apostrofosAbove = this.findAbove(g, 'apostrofos');
      const elafronAbove = this.findAbove(g, 'elafron');
      const hasElafronApostrofosAbove = this.hasAbove(g, 'elafron_apostrofos');

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

      if (this.hasAbove(g, 'yporroe')) {
        return QuantitativeNeume.OligonPlusHyporoePlusKentemata;
      }

      if (this.hasAbove(g, 'hamili')) {
        return QuantitativeNeume.OligonPlusHamiliPlusKentemata;
      }

      const ypsili = this.findAbove(g, 'ypsili');

      if (ypsili.length === 1) {
        if (
          Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
          Math.abs(
            ypsili[0].bounding_circle.x -
              (g.base.bounding_rect.x + g.base.bounding_rect.w),
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
      const ypsili = this.findAbove(g, 'ypsili');

      if (ypsili.length === 1) {
        if (
          Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
          Math.abs(
            ypsili[0].bounding_circle.x -
              (g.base.bounding_rect.x + g.base.bounding_rect.w),
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
              g.base.bounding_circle.x - g.base.bounding_rect.w / 4,
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
    const ypsili = this.findAbove(g, 'ypsili');

    if (ypsili.length === 1) {
      const neume = ypsili[0];

      if (
        Math.abs(neume.bounding_circle.x - g.base.bounding_rect.x) <
        Math.abs(
          neume.bounding_circle.x -
            (g.base.bounding_rect.x + g.base.bounding_rect.w),
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
    if (this.hasAbove(g, 'ison')) {
      return QuantitativeNeume.OligonPlusIson;
    }

    if (this.hasAbove(g, 'apostrofos')) {
      return QuantitativeNeume.OligonPlusApostrophos;
    }

    if (this.hasAbove(g, 'yporroe')) {
      return QuantitativeNeume.OligonPlusHyporoe;
    }

    const apostrofosAbove = this.hasAbove(g, 'apostrofos');
    const elafronAbove = this.hasAbove(g, 'elafron');
    const elafronApostrofosAbove = this.hasAbove(g, 'elafron_apostrofos');

    if (apostrofosAbove && !elafronAbove) {
      return QuantitativeNeume.OligonPlusApostrophos;
    }

    if (!apostrofosAbove && elafronAbove) {
      return QuantitativeNeume.OligonPlusElaphron;
    }

    if (elafronApostrofosAbove || (elafronAbove && apostrofosAbove)) {
      return QuantitativeNeume.OligonPlusElaphronPlusApostrophos;
    }

    if (this.hasAbove(g, 'hamili')) {
      return QuantitativeNeume.OligonPlusHamili;
    }

    return QuantitativeNeume.Oligon;
  }

  processOligonWithMiddleKentima(g: NeumeGroup) {
    // Check kentima above
    const kentimaAbove = this.findAbove(g, 'kentima');

    // Handle oligon + kentemata
    if (kentimaAbove.length >= 2) {
      return QuantitativeNeume.OligonKentimaMiddleKentimata;
    }

    return QuantitativeNeume.OligonPlusKentima;
  }

  processPetaste(g: NeumeGroup) {
    // Check kentima above
    const kentimaAbove = this.findAbove(g, 'kentima');

    // Handle petaste + ypsili + kentemata
    if (kentimaAbove.length >= 2) {
      const ypsili = this.findAbove(g, 'ypsili');

      if (ypsili.length === 2) {
        return QuantitativeNeume.PetastiKentimataDoubleYpsili;
      }

      if (ypsili.length >= 3) {
        return QuantitativeNeume.PetastiKentimataTripleYpsili;
      }
    }

    // Handle petaste with single kentima
    if (kentimaAbove.length == 1) {
      const ypsili = this.findAbove(g, 'ypsili');

      if (ypsili.length === 1) {
        if (
          Math.abs(ypsili[0].bounding_circle.x - g.base.bounding_rect.x) <
          Math.abs(
            ypsili[0].bounding_circle.x -
              (g.base.bounding_rect.x + g.base.bounding_rect.w),
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
              g.base.bounding_circle.x - g.base.bounding_rect.w / 4,
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
    const ypsili = this.findAbove(g, 'ypsili');

    if (ypsili.length === 1) {
      const neume = ypsili[0];

      if (
        Math.abs(neume.bounding_circle.x - g.base.bounding_rect.x) <
        Math.abs(
          neume.bounding_circle.x -
            (g.base.bounding_rect.x + g.base.bounding_rect.w),
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
    if (this.hasAbove(g, 'ison')) {
      return QuantitativeNeume.PetastiWithIson;
    }

    if (this.hasAbove(g, 'oligon')) {
      return QuantitativeNeume.PetastiPlusOligon;
    }

    if (this.hasAbove(g, 'yporroe')) {
      return QuantitativeNeume.PetastiPlusHyporoe;
    }

    const hamili = this.findAbove(g, 'hamili');

    if (hamili.length === 1) {
      const apostrofos = this.has(g, 'apostrofos');
      const elafron = this.has(g, 'apostrofos');
      const elafronApostrofos = this.has(g, 'elafron_apostrofos');

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
      if (this.has(g, 'apostrofos')) {
        return QuantitativeNeume.PetastiDoubleHamiliApostrofos;
      }

      return QuantitativeNeume.PetastiDoubleHamili;
    }

    const apostrofosAbove = this.hasAbove(g, 'apostrofos');
    const elafronAbove = this.hasAbove(g, 'elafron');
    const elafronApostrofosAbove = this.hasAbove(g, 'elafron_apostrofos');

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

  processHamili(g: NeumeGroup) {
    // Check for extra hamili
    const hamili = this.find(g, 'hamli');

    // Handle double hamili
    if (hamili.length === 1) {
      const apostrofos = this.has(g, 'apostrofos');
      const elafron = this.has(g, 'apostrofos');
      const elafronApostrofos = this.has(g, 'elafron_apostrofos');

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

    const apostrofosAbove = this.hasAbove(g, 'apostrofos');
    const elafronAbove = this.hasAbove(g, 'elafron');
    const elafronApostrofosAbove = this.hasAbove(g, 'elafron_apostrofos');

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

  applySanityChecks(g: NeumeGroup, segmentation: Segmentation) {
    const confidence = (matches: AugmentedContourMatch[]) =>
      Math.max(...matches.map((x) => x.confidence));

    // Filter out apli that are too low
    for (const x of this.findBelow(g, 'apli')) {
      if (
        x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h) >=
        segmentation.oligon_height * 2
      ) {
        const index = g.support.indexOf(x);

        if (index !== -1) {
          g.support.splice(index, 1);
        }
      }
    }

    // Filter out kentimata that are too low
    for (const x of this.findBelow(g, 'kentima')) {
      if (
        x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h) >=
        segmentation.oligon_height * 2
      ) {
        const index = g.support.indexOf(x);

        if (index !== -1) {
          g.support.splice(index, 1);
        }
      }
    }

    // Filter out gorgons that are too high
    for (let x of this.findAbove(g, 'gorgon')) {
      if (
        g.base.bounding_rect.y - (x.bounding_rect.y + x.bounding_rect.h) >
        0.75 * segmentation.oligon_width
      ) {
        const index = g.support.indexOf(x);

        if (index !== -1) {
          g.support.splice(index, 1);
        }
      }
    }

    // Filter out gorgon that are too low
    for (const x of this.findBelow(g, 'gorgon')) {
      if (
        x.bounding_rect.y - (g.base.bounding_rect.y + g.base.bounding_rect.h) >=
        segmentation.oligon_height * 2
      ) {
        const index = g.support.indexOf(x);

        if (index !== -1) {
          g.support.splice(index, 1);
        }
      }
    }

    // If there is both a klasma and apli,
    // use the confidence as a tie breaker
    let apli = this.findBelow(g, 'apli');
    let klasma = this.find(g, 'klasma');

    if (apli.length > 0 && klasma.length > 0) {
      if (confidence(klasma) > confidence(apli)) {
        g.support = g.support.filter((x) => x.label != 'apli');
      } else {
        g.support = g.support.filter((x) => x.label != 'klasma');
      }
    }

    // If the group has both a gorgon and klasma,
    // this is probably wrong. So take the highest confidence only.
    let gorgon = this.find(g, 'gorgon');
    klasma = this.find(g, 'klasma');

    if (gorgon.length > 0 && klasma.length > 0) {
      if (confidence(klasma) > confidence(gorgon)) {
        g.support = g.support.filter((x) => x.label != 'gorgon');
      } else {
        g.support = g.support.filter((x) => x.label != 'klasma');
      }
    }

    // If the group has both a gorgon and apli,
    // this is probably wrong. So take the highest confidence only.
    apli = this.findBelow(g, 'apli');
    gorgon = this.find(g, 'gorgon');

    if (gorgon.length > 0 && apli.length > 0) {
      if (confidence(apli) > confidence(gorgon)) {
        g.support = g.support.filter((x) => x.label != 'gorgon');
      } else {
        g.support = g.support.filter((x) => x.label != 'apli');
      }
    }

    // If the group has both a gorgon/apli and psifiston,
    // this is probably wrong. So take the highest confidence only.
    let psifiston = this.findBelow(g, 'psifiston');
    gorgon = this.find(g, 'gorgon');

    if (psifiston.length > 0 && gorgon.length > 0) {
      if (confidence(psifiston) > confidence(gorgon)) {
        g.support = g.support.filter((x) => x.label != 'gorgon');
      } else {
        g.support = g.support.filter((x) => x.label != 'psifiston');
      }
    }

    psifiston = this.findBelow(g, 'psifiston');
    apli = this.findBelow(g, 'apli');

    if (psifiston.length > 0 && apli.length > 0) {
      if (confidence(psifiston) > confidence(apli)) {
        g.support = g.support.filter((x) => x.label != 'apli');
      } else {
        g.support = g.support.filter((x) => x.label != 'psifiston');
      }
    }
  }

  applyAntikenoma(e: NoteElement, g: NeumeGroup) {
    if (this.hasBelow(g, 'antikenoma', 0.5)) {
      e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
    } else if (this.hasBelow(g, 'antikenoma_apli', 0.5)) {
      e.vocalExpressionNeume = VocalExpressionNeume.Antikenoma;
      e.timeNeume = TimeNeume.Hapli;
    }
  }

  applyGorgon(e: NoteElement, g: NeumeGroup) {
    const gorgon = this.find(g, 'gorgon', 0.5);

    // TODO secondary/tertiary gorgons

    if (gorgon.length > 0) {
      e.gorgonNeume =
        gorgon[0].bounding_circle.y <= g.base.bounding_circle.y
          ? GorgonNeume.Gorgon_Top
          : GorgonNeume.Gorgon_Bottom;
    }
  }

  applyDigorgon(e: NoteElement, g: NeumeGroup) {
    const support = g.support?.find((x) => x.label === 'digorgon');

    // TODO secondary/tertiary gorgons

    if (support) {
      e.gorgonNeume = GorgonNeume.Digorgon;
    }
  }

  applyTrigorgon(e: NoteElement, g: NeumeGroup) {
    const support = g.support?.find((x) => x.label === 'digorgon');

    // TODO secondary/tertiary gorgons

    if (support) {
      e.gorgonNeume = GorgonNeume.Digorgon;
    }
  }

  applyKlasma(e: NoteElement, g: NeumeGroup) {
    const support = g.support?.find((x) => x.label === 'klasma');

    if (support) {
      e.timeNeume =
        support.bounding_circle.y <= g.base.bounding_circle.y
          ? TimeNeume.Klasma_Top
          : TimeNeume.Klasma_Bottom;
    }
  }

  applyApli(e: NoteElement, g: NeumeGroup) {
    const apli = this.findBelow(g, 'apli');

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

  applyFthora(e: NoteElement | MartyriaElement, g: NeumeGroup) {
    const fthora = g.support?.find((x) => x.label.startsWith('fthora'));

    // TODO secondary/tertiary gorgons

    if (fthora) {
      if (fthora.bounding_rect.y < g.base.bounding_rect.y) {
        if (fthora.label === 'fthora_diatonic_di') {
          e.fthora = Fthora.DiatonicThi_Top;
        } else if (fthora.label === 'fthora_diatonic_ke') {
          e.fthora = Fthora.DiatonicKe_Top;
        } else if (fthora.label === 'fthora_diatonic_pa') {
          e.fthora = Fthora.DiatonicPa_Top;
        } else if (fthora.label === 'fthora_enharmonic') {
          e.fthora = Fthora.Enharmonic_Top;
        } else if (fthora.label === 'fthora_hard_chromatic_di') {
          e.fthora = Fthora.HardChromaticThi_Top;
        } else if (fthora.label === 'fthora_hard_chromatic_pa') {
          e.fthora = Fthora.HardChromaticPa_Top;
        } else if (fthora.label === 'fthora_soft_chromatic_di') {
          e.fthora = Fthora.SoftChromaticThi_Top;
        }
      } else {
        if (fthora.label === 'fthora_diatonic_di') {
          e.fthora = Fthora.DiatonicThi_Bottom;
        } else if (fthora.label === 'fthora_diatonic_ke') {
          e.fthora = Fthora.DiatonicKe_Bottom;
        } else if (fthora.label === 'fthora_diatonic_pa') {
          e.fthora = Fthora.DiatonicPa_Bottom;
        } else if (fthora.label === 'fthora_enharmonic') {
          e.fthora = Fthora.Enharmonic_Bottom;
        } else if (fthora.label === 'fthora_hard_chromatic_di') {
          e.fthora = Fthora.HardChromaticThi_Bottom;
        } else if (fthora.label === 'fthora_hard_chromatic_pa') {
          e.fthora = Fthora.HardChromaticPa_Bottom;
        } else if (fthora.label === 'fthora_soft_chromatic_di') {
          e.fthora = Fthora.SoftChromaticThi_Bottom;
        }
      }
    }
  }

  applyPsifiston(e: NoteElement, g: NeumeGroup) {
    if (this.hasBelow(g, 'psifiston', 0.75)) {
      e.vocalExpressionNeume = VocalExpressionNeume.Psifiston;
    }
  }

  applyHeteron(e: NoteElement, g: NeumeGroup) {
    const heteron = this.findBelow(g, 'heteron', 0);
    if (heteron.length > 0) {
      if (heteron[0].bounding_rect.x > g.base.bounding_rect.x) {
        // TODO figure out if it's connecting or not
        // Probably need to be able to detect apli before we can do this.
        e.vocalExpressionNeume = VocalExpressionNeume.HeteronConnecting;
      }
    }
  }

  applyHomalon(e: NoteElement, g: NeumeGroup) {
    const homalon = this.findBelow(g, 'omalon', 0);
    if (homalon.length > 0) {
      if (homalon[0].bounding_rect.x > g.base.bounding_rect.x) {
        if (this.hasAbove(g, 'klasma')) {
          e.vocalExpressionNeume = VocalExpressionNeume.Homalon;
        } else {
          e.vocalExpressionNeume = VocalExpressionNeume.HomalonConnecting;
        }
      }
    }
  }

  applyEndofonon(e: NoteElement, g: NeumeGroup) {
    const endofonon = this.findBelow(g, 'endofonon', 0);
    if (endofonon.length > 0) {
      if (endofonon[0].bounding_rect.x > g.base.bounding_rect.x) {
        e.vocalExpressionNeume = VocalExpressionNeume.Endofonon;
      }
    }
  }

  applyStavros(e: NoteElement, g: NeumeGroup) {
    const stavros = this.has(g, 'stavros', 0);
    if (stavros) {
      e.vocalExpressionNeume = VocalExpressionNeume.Cross_Top;
    }
  }

  is_base(label: string) {
    return [
      'ison',
      'oligon',
      'petaste',
      'apostrofos',
      'elafron',
      'elafron_apostrofos',
      'vareia',
      'kentima',
      'yporroe',
    ].includes(label);
  }

  isFthoraMartyria(label: string) {
    return ['fthora_hard_chromatic_di'].includes(label);
  }

  touches_baseline(match: ContourMatch, baseline: number) {
    return (
      match.bounding_rect.y <= baseline &&
      baseline <= match.bounding_rect.y + match.bounding_rect.h
    );
  }

  centerOverlaps(base: AugmentedContourMatch, support: AugmentedContourMatch) {
    return (
      base.bounding_rect.x <= support.bounding_circle.x &&
      support.bounding_circle.x <= base.bounding_rect.x + base.bounding_rect.w
    );
  }

  overlaps(base: ContourMatch, support: ContourMatch, threshold: number) {
    const left = Math.max(base.bounding_rect.x, support.bounding_rect.x);
    const right = Math.min(
      base.bounding_rect.x + base.bounding_rect.w,
      support.bounding_rect.x + support.bounding_rect.w,
    );

    return (right - left) / support.bounding_rect.w >= threshold;
  }

  findAbove(g: NeumeGroup, label: string, threshold = 1) {
    return g.support.filter(
      (x) =>
        x.bounding_rect.y < g.base.bounding_rect.y &&
        x.label === label &&
        (this.centerOverlaps(g.base, x) || this.overlaps(g.base, x, threshold)),
    );
  }

  findBelow(g: NeumeGroup, label: string, threshold = 1) {
    return g.support.filter(
      (x) =>
        x.bounding_rect.y > g.base.bounding_rect.y &&
        x.label === label &&
        (this.centerOverlaps(g.base, x) || this.overlaps(g.base, x, threshold)),
    );
  }

  find(g: NeumeGroup, label: string, threshold = 1) {
    return g.support.filter(
      (x) =>
        x.label === label &&
        (this.centerOverlaps(g.base, x) || this.overlaps(g.base, x, threshold)),
    );
  }

  hasAbove(g: NeumeGroup, label: string, threshold = 1) {
    return this.findAbove(g, label, threshold).length > 0;
  }

  hasBelow(g: NeumeGroup, label: string, threshold = 1) {
    return this.findBelow(g, label, threshold).length > 0;
  }

  has(g: NeumeGroup, label: string, threshold = 1) {
    return this.find(g, label, threshold).length > 0;
  }

  findSupport(
    g: NeumeGroup,
    matches: AugmentedContourMatch[],
    startIndex: number,
  ) {
    const m = matches[startIndex];
    // Find the supporting neumes to the right
    for (let i = startIndex + 1; i < matches.length; i++) {
      const s = matches[i];

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
    for (let i = startIndex - 1; i >= 0; i--) {
      const s = matches[i];

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

  findBase(matches: AugmentedContourMatch[], startIndex: number) {
    const m = matches[startIndex];
    // Search for a base to the right
    for (let i = startIndex + 1; i < matches.length; i++) {
      const s = matches[i];

      // Stop if we are not on the same line number
      if (s.line != m.line) {
        break;
      }

      // If we find a base, check whether it overlaps.
      // If it doesn't, stop searching.
      if (s.isBase || this.is_base(s.label)) {
        if (
          s.bounding_rect.x <= m.bounding_circle.x &&
          m.bounding_circle.x <= s.bounding_rect.x + s.bounding_rect.w
        ) {
          return s;
        } else {
          break;
        }
      }
    }

    // Find the supporting neumes to the left
    for (let i = startIndex - 1; i >= 0; i--) {
      const s = matches[i];

      // Stop if we are not on the same line number
      if (s.line != m.line) {
        break;
      }

      // If we find a base, check whether it overlaps.
      // If it doesn't, stop searching.
      if (s.isBase || this.is_base(s.label)) {
        if (
          s.bounding_rect.x <= m.bounding_circle.x &&
          m.bounding_circle.x <= s.bounding_rect.x + s.bounding_rect.w
        ) {
          return s;
        } else {
          break;
        }
      }
    }
  }

  groupMatches(analysis: PageAnalysis, options: OcrImporterOptions) {
    const groups: NeumeGroup[] = [];

    // Filter out bad matches and convert the remaining matches
    // into our augmented data model
    const matches = analysis.matches
      .filter(
        (x) =>
          x.line >= 0 &&
          x.label != null &&
          x.confidence > options.min_confidence_threshold,
      )
      .map((x) => new AugmentedContourMatch(x));

    // Form groups. There are two types of groups:
    // 1) Base neumes that touch the baseline
    // 2) Martyria
    // 3) Kronos
    for (const [i, m] of matches.entries()) {
      // TODO the condition "touches_baseline" can sometimes cause
      // true base neumes to be filtered out if, for example, a line contains a single
      // apostrofos followed by a hard chromatic martyria. This can cause the base line detection
      // to mistakenly place the base line lower than it should.
      m.isBase =
        this.is_base(m.label) &&
        this.touches_baseline(m, analysis.segmentation.baselines[m.line]);

      m.isMartyria =
        m.label.startsWith('martyria') &&
        !m.label.startsWith('martyria_root') &&
        m.confidence > options.martyria_confidence_threshold;

      m.isKronos = m.label === 'kronos';

      if (m.isBase) {
        const g = new NeumeGroup();
        groups.push(g);
        g.base = m;

        this.findSupport(g, matches, i);
      } else if (m.isMartyria || m.isKronos) {
        // We only trust this prediction if there is no base neume above or below it.
        if (!this.findBase(matches, i)) {
          const g = new NeumeGroup();
          g.base = m;
          this.findSupport(g, matches, i);
          groups.push(g);
        }
      } else if (
        this.isFthoraMartyria(m.label) &&
        m.confidence > options.martyria_confidence_threshold
      ) {
        // If this match is neume that could be both a martyria
        // or a fthora, we must check its support. If it has
        // base in the support, then it's a fthora. Otherwise it is a
        // martyria.
        if (!this.findBase(matches, i)) {
          const g = new NeumeGroup();
          g.base = m;
          m.isMartyria = true;
          this.findSupport(g, matches, i);
          groups.push(g);
        }
      }
    }

    return groups;
  }

  processAnalysis(analysis: OcrAnalysis, options: OcrImporterOptions) {
    const elements: ScoreElement[] = [];

    for (let page of analysis.pages) {
      for (let e of this.processPageAnalysis(page, options)) {
        elements.push(e);
      }
    }

    return elements;
  }

  processPageAnalysis(analysis: PageAnalysis, options: OcrImporterOptions) {
    const elements: ScoreElement[] = [];

    const groups = this.groupMatches(analysis, options);

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

      this.applySanityChecks(g, analysis.segmentation);

      if (g.base.isBase) {
        const e = new NoteElement();

        if (g.base.label === 'oligon') {
          if (
            next?.base.line === g.base.line &&
            next?.base.label === 'kentima' &&
            (nextNext?.base.label !== 'kentima' ||
              nextNext?.base.line !== g.base.line)
          ) {
            // Combine the kentima with the oligon and skip ahead
            g.support.push(...next.support);
            i++;
            e.quantitativeNeume = this.processOligonWithMiddleKentima(g);
          } else {
            e.quantitativeNeume = this.processOligon(g);
          }
        } else if (g.base.label === 'ison') {
          e.quantitativeNeume = this.processIson(g);
        } else if (g.base.label === 'petaste') {
          e.quantitativeNeume = this.processPetaste(g);
        } else if (g.base.label === 'apostrofos') {
          e.quantitativeNeume = this.processApostrofos(g);

          if (
            e.quantitativeNeume === QuantitativeNeume.Apostrophos &&
            next?.base.line === g.base.line &&
            next?.base.label === 'elafron'
          ) {
            // Combine the apostrofos with the elafron
            e.quantitativeNeume = QuantitativeNeume.RunningElaphron;
            g.support.push(...next.support);
            i++;
          } else if (
            e.quantitativeNeume === QuantitativeNeume.Apostrophos &&
            next?.base.line === g.base.line &&
            next?.base.label === 'petaste' &&
            this.hasAbove(next, 'elafron')
          ) {
            // Combine the apostrofos with the petasti+elafron
            e.quantitativeNeume = QuantitativeNeume.PetastiPlusRunningElaphron;
            g.support.push(...next.support);
            i++;
          }
        } else if (g.base.label === 'yporroe') {
          e.quantitativeNeume = QuantitativeNeume.Hyporoe;
        } else if (g.base.label === 'elafron') {
          e.quantitativeNeume = QuantitativeNeume.Elaphron;

          const apostrofos = this.find(g, 'apostrofos');

          if (apostrofos.length > 0) {
            e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

            // Sometimes the apostrofos is double detected
            if (next?.base === apostrofos[0]) {
              g.support.push(...next.support);
              i++;
            }
          }
        } else if (g.base.label === 'elafron_apostrofos') {
          e.quantitativeNeume = QuantitativeNeume.ElaphronPlusApostrophos;

          const apostrofos = this.find(g, 'apostrofos');

          // Sometimes the apostrofos is double detected
          if (apostrofos.length > 0) {
            if (next?.base === apostrofos[0]) {
              g.support.push(...next.support);
              i++;
            }
          }
        } else if (g.base.label === 'hamili') {
          e.quantitativeNeume = this.processHamili(g);
        } else if (g.base.label === 'kentima') {
          if (
            next?.base.line === g.base.line &&
            next?.base.label === 'kentima'
          ) {
            e.quantitativeNeume = QuantitativeNeume.Kentemata;
            g.support.push(...next.support);
            i++;
          }
        } else if (g.base.label === 'vareia') {
          vareia = true;
          this.applyGorgon(e, g);
          // TODO process apli
          continue;
        } else if (g.base.label === 'stavros') {
          e.quantitativeNeume = QuantitativeNeume.Cross;
        }

        this.applyAntikenoma(e, g);
        this.applyGorgon(e, g);
        this.applyDigorgon(e, g);
        this.applyTrigorgon(e, g);
        this.applyApli(e, g);
        this.applyKlasma(e, g);
        this.applyFthora(e, g);
        this.applyPsifiston(e, g);
        this.applyHeteron(e, g);
        this.applyHomalon(e, g);
        this.applyEndofonon(e, g);
        this.applyStavros(e, g);

        if (vareia) {
          e.vareia = true;
          vareia = false;
        }

        elements.push(e);
      } else if (g.base.isMartyria) {
        // TODO make this smarter
        const e = new MartyriaElement();
        e.auto = true;
        elements.push(e);

        // If the martyria is the last neume group on the line...
        if (g.base.line !== next?.base.line) {
          // if it is more than 2 * oligon_width away from the previous neume,
          // we assume it is a right aligned martyria.
          if (
            prev != null &&
            g.base.line === prev.base.line &&
            g.base.bounding_rect.x -
              (prev.base.bounding_rect.x + prev.base.bounding_rect.w) >=
              analysis.segmentation.oligon_width * 2
          ) {
            e.alignRight = true;
          }

          // Otherwise, put a line break on this martyria.
          if (!e.alignRight && g.base.line !== next?.base.line) {
            e.lineBreak = true;
            e.lineBreakType = LineBreakType.Left;
          }
        }

        this.applyFthora(e, g);
      } else if (g.base.isKronos) {
        const e = new TempoElement();
        elements.push(e);

        if (this.has(g, 'gorgon') && this.has(g, 'argon')) {
          e.neume = TempoSign.Medium;
        } else if (this.has(g, 'gorgon')) {
          e.neume = TempoSign.Quick;
        } else if (this.has(g, 'digorgon')) {
          e.neume = TempoSign.Quicker;
        } else if (this.has(g, 'trigorgon')) {
          e.neume = TempoSign.VeryQuick;
        } else if (this.has(g, 'argon')) {
          e.neume = TempoSign.Moderate;
        } else if (this.has(g, 'diargon')) {
          e.neume = TempoSign.Slow;
        } else if (this.has(g, 'triargon')) {
          e.neume = TempoSign.Slower;
        }
      }
    }

    return elements;
  }
}
