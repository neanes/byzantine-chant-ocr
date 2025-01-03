import { ContourMatch, OcrClass } from './OcrAnalysis';

export class AugmentedContourMatch extends ContourMatch {
  public isBase: boolean = false;
  public isMartyria: boolean = false;
  public isKronos: boolean = false;
  public label: OcrClass = 'oligon';

  constructor(match?: ContourMatch) {
    super();

    if (match) {
      Object.assign(this, match);
    }
  }
}
export class NeumeGroup {
  public base: AugmentedContourMatch = new AugmentedContourMatch();
  public support: AugmentedContourMatch[] = [];
}
