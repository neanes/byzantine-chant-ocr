import {
  ElementType,
  NoteElement,
  ScoreElement,
} from '../../integrations/neanes/neanes/models/Element';
import {
  Neume,
  QuantitativeNeume,
} from '../../integrations/neanes/neanes/models/Neumes';
import { NeumeGroup } from '../../integrations/neanes/OcrImportCustomModels';

export class ElementWithIssues {
  public actualIndex: Number;
  public expectedIndex: Number;
  public expectedBase: QuantitativeNeume;
  public ocrNeumeGroup: NeumeGroup | null;
  public issues: Issue[] = [];

  constructor(expected: NoteElement, actual: NoteElement, issues: Issue[]) {
    this.actualIndex = actual.index;
    this.expectedIndex = expected.index;
    this.expectedBase = expected.quantitativeNeume;
    this.issues = issues;
    this.ocrNeumeGroup = actual.ocrNeumeGroup;
  }
}

export enum IssueType {
  Accidental = 'accidental',
  BaseSubstitution = 'base_substitution',
  Fthora = 'fthora',
  Gorgon = 'gorgon',
  Quality = 'quality',
  Time = 'time',
  Vareia = 'vareia',
}

export class Issue {
  public type: IssueType;
  public expected: Neume;
  public actual: Neume;

  constructor(type, expected, actual) {
    this.type = type;
    this.actual = actual;
    this.expected = expected;
  }
}

export class Scores {
  public gorgon = 0;
  public quality = 0;
  public vareia = 0;
  public time = 0;
  public accidental = 0;
  public fthora = 0;

  get total() {
    return this.gorgon + this.quality + this.vareia + this.time;
  }
}

function score(
  expected: NoteElement,
  actual: NoteElement,
  penalties: Scores,
  totals: Scores,
) {
  const issues: Issue[] = [];

  // Gorgon
  if (expected.gorgonNeume != null || actual.gorgonNeume != null) {
    totals.gorgon += 1;
  }

  if (expected.gorgonNeume !== actual.gorgonNeume) {
    penalties.gorgon += 1;

    issues.push(
      new Issue(IssueType.Gorgon, expected.gorgonNeume, actual.gorgonNeume),
    );
  }

  // Vocal Expression (Quality)
  if (
    expected.vocalExpressionNeume != null ||
    actual.vocalExpressionNeume != null
  ) {
    totals.quality += 1;
  }

  if (expected.vocalExpressionNeume !== actual.vocalExpressionNeume) {
    penalties.quality += 1;
    issues.push(
      new Issue(
        IssueType.Quality,
        expected.vocalExpressionNeume,
        actual.vocalExpressionNeume,
      ),
    );
  }

  // Time
  if (expected.timeNeume != null || actual.timeNeume != null) {
    totals.time += 1;
  }

  if (expected.timeNeume !== actual.timeNeume) {
    penalties.time += 1;
    issues.push(
      new Issue(IssueType.Time, expected.timeNeume, actual.timeNeume),
    );
  }

  // Accidentals
  if (expected.accidental != null || actual.accidental != null) {
    totals.accidental += 1;
  }

  if (expected.accidental !== actual.accidental) {
    penalties.accidental += 1;
    issues.push(
      new Issue(IssueType.Accidental, expected.accidental, actual.accidental),
    );
  }

  // Fthora
  if (expected.fthora != null || actual.fthora != null) {
    totals.fthora += 1;
  }

  if (expected.fthora !== actual.fthora) {
    penalties.fthora += 1;
    issues.push(new Issue(IssueType.Fthora, expected.fthora, actual.fthora));
  }

  // Vareia
  if (expected.vareia || actual.vareia) {
    totals.vareia += 1;
  }

  if (expected.vareia !== actual.vareia) {
    penalties.vareia += 1;
    issues.push(new Issue(IssueType.Vareia, expected.vareia, actual.vareia));
  }

  return issues;
}

export function calculateScorecard(
  expectedElements: ScoreElement[],
  actualElements: ScoreElement[],
) {
  const penalties = new Scores();
  const totals = new Scores();
  const elementsWithIssues: ElementWithIssues[] = [];

  for (let i = 0; i < expectedElements.length; i++) {
    if (
      expectedElements[i].elementType === ElementType.Empty ||
      actualElements[i].elementType === ElementType.Empty
    ) {
      continue;
    }

    const expected = expectedElements[i] as NoteElement;
    const actual = actualElements[i] as NoteElement;

    const issues = score(
      expected as NoteElement,
      actual as NoteElement,
      penalties,
      totals,
    );

    // Log substitutions
    // TODO log deletion/insertions, too?
    if (expected.quantitativeNeume !== actual.quantitativeNeume) {
      issues.push(
        new Issue(
          IssueType.BaseSubstitution,
          expected.quantitativeNeume,
          actual.quantitativeNeume,
        ),
      );
    }

    if (issues.length > 0) {
      elementsWithIssues.push(
        new ElementWithIssues(
          expected as NoteElement,
          actual as NoteElement,
          issues,
        ),
      );
    }
  }

  const similarities = new Scores();

  similarities.gorgon = 1 - penalties.gorgon / totals.gorgon;
  similarities.time = 1 - penalties.time / totals.time;
  similarities.vareia = 1 - penalties.vareia / totals.vareia;
  similarities.quality = 1 - penalties.quality / totals.quality;
  similarities.accidental = 1 - penalties.accidental / totals.accidental;
  similarities.fthora = 1 - penalties.fthora / totals.fthora;

  const similarity = 1 - penalties.total / totals.total;

  return { penalties, totals, similarities, similarity, elementsWithIssues };
}
