import { ContourMatch } from "./OcrAnalysis";

export class AugmentedContourMatch extends ContourMatch {
  public isBase: boolean = false;
  public isGrouped: boolean = false;

  constructor(match: ContourMatch) {
    super();
    Object.assign(this, match);
  }
}

export class NeumeGroup {
  public base: ContourMatch = new ContourMatch();
  public support: ContourMatch[] = [];
  public complete: boolean = false;
}
