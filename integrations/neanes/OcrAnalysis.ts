export class OcrAnalysis {
  public model_metadata: ModelMetadata = new ModelMetadata();
  public pages: PageAnalysis[] = [];
}

export class ModelMetadata {
  public model_version: string = '';
  public classes: OcrClass[] = [];
}

export class PageAnalysis {
  public id: number = 0;
  public original_page_num?: number;
  public page_area?: 'left' | 'right';

  public segmentation: Segmentation = new Segmentation();
  public matches: ContourMatch[] = [];
}

export class Segmentation {
  public page_width: number = 0;
  public page_height: number = 0;
  public oligon_width: number = 0;
  public oligon_height: number = 0;
  public avg_text_height: number = 0;
  public baselines: number[] = [];
  public textlines: number[] = [];
  public textlines_adj: number[] = [];
}

export class ContourMatch {
  public id: number = 0;
  public bounding_circle: Circle = new Circle();
  public bounding_rect: Rect = new Rect();
  public label: OcrClass | null = null;
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

export type OcrClass =
  | 'antikenoma'
  | 'antikenoma_apli'
  | 'apli'
  | 'apostrofos'
  | 'argon'
  | 'breath'
  | 'digorgon'
  | 'elafron'
  | 'elafron_apostrofos'
  | 'elafron_syndesmos'
  | 'flat_2'
  | 'flat_4'
  | 'flat_general'
  | 'fthora_diatonic_di'
  | 'fthora_diatonic_ke'
  | 'fthora_diatonic_ni'
  | 'fthora_diatonic_ni_high'
  | 'fthora_diatonic_pa'
  | 'fthora_diatonic_vou'
  | 'fthora_enharmonic'
  | 'fthora_hard_chromatic_di'
  | 'fthora_hard_chromatic_pa'
  | 'fthora_kliton'
  | 'fthora_soft_chromatic_di'
  | 'fthora_zygos'
  | 'gorgon'
  | 'hamili'
  | 'heteron'
  | 'ison'
  | 'ison_di'
  | 'ison_ke'
  | 'ison_low'
  | 'ison_ni'
  | 'ison_pa'
  | 'ison_unison'
  | 'kentima'
  | 'klasma'
  | 'kronos'
  | 'martyria_diatonic_di'
  | 'martyria_diatonic_ga'
  | 'martyria_diatonic_ke'
  | 'martyria_diatonic_vou'
  | 'martyria_diatonic_zo_low'
  | 'martyria_root_di'
  | 'martyria_root_pa'
  | 'martyria_root_vou'
  | 'martyria_soft_chromatic_di'
  | 'num_2'
  | 'num_3'
  | 'num_4'
  | 'oligon'
  | 'omalon'
  | 'paren_left'
  | 'paren_right'
  | 'petaste'
  | 'psifiston'
  | 'sharp_2'
  | 'sharp_general'
  | 'stavros'
  | 'trigorgon'
  | 'vareia'
  | 'yporroe'
  | 'ypsili';
