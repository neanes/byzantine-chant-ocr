import { ContourMatch } from "./OcrAnalysis";

export class AugmentedContourMatch extends ContourMatch {
  public isBase: boolean = false;
  public isMartyria: boolean = false;
  public isKronos: boolean = false;

  constructor(match?: ContourMatch) {
    super();

    if (match) {
      Object.assign(this, match);
    }
  }
}

export class ContourLineGroup {
  public onBaseline: AugmentedContourMatch[] = [];
  public aboveBaseline: AugmentedContourMatch[] = [];
  public belowBaseline: AugmentedContourMatch[] = [];
}

export class NeumeGroup {
  public base: AugmentedContourMatch = new AugmentedContourMatch();
  public support: AugmentedContourMatch[] = [];
}
