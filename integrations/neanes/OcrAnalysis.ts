export class OcrAnalysis {
  public model_version: string = "";
  public segmentation: Segmentation = new Segmentation();
  public matches: ContourMatch[] = [];
}

export class Segmentation {
  public oligon_height: number = 0;
  public oligon_width: number = 0;
  public avg_text_height: number = 0;
  public baselines: number[] = [];
  public textlines: number[] = [];
  public textlines_adj: number[] = [];
}

export class ContourMatch {
  public bounding_circle: Circle = new Circle();
  public bounding_rect: Rect = new Rect();
  public label: string = "";
  public confidence: number = 0;
  public line: number = 0;
}

export class Rect {
  public x: number = 0;
  public y: number = 0;
  public w: number = 0;
  public h: number = 0;
}

export class Circle {
  public x: number = 0;
  public y: number = 0;
  public r: number = 0;
}
