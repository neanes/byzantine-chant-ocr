import { promises as fs } from 'fs';
import { afterAll, expect, test } from '@jest/globals';

import { OcrImporter } from '../integrations/neanes/OcrImporter';
import { extractQuantitativeNeumes } from './util/extractQuantitativeNeumes';
import { launchOcr } from './util/launchOcr';
import { backtrackAlignment, levenshteinDistance } from './util/levenshtein';
import { SaveService } from '../integrations/neanes/neanes/services/SaveService';
import {
  ElementType,
  NoteElement,
} from '../integrations/neanes/neanes/models/Element';
import { calculateScorecard, Scores } from './util/neumeCompare';
import { fileExists } from './util/fileExists';

// If you are tweaking only the importer, set the SKIP_OCR=true as an environment variable
// to bypass re-generating the YAML files every time you run the tests.
const skipOcr = process.env.SKIP_OCR === 'true';

const levenshteinDistanceThreshold = 0.9;
const timeoutInMs = 120 * 1000;
const reportFilePath = 'OcrImporter.report.json';
const report: Array<{
  testName: string;
  page: string;
  levenshteinDistance: number;
  similarity: number;
  scorecard: {
    penalties: Scores;
    totals: Scores;
    similarities: Scores;
    similarity: number;
  };
}> = [];

// Write the report after all tests have completed
afterAll(async () => {
  await fs.writeFile(reportFilePath, JSON.stringify(report, null, 2));
});

const table = [
  {
    page: 'anastasimatarion_john_p0011',
  },
  {
    page: 'heirmologion_john_p0120',
  },
];

test.each(table)(
  'OCR $page',
  async ({ page }) => {
    // Arrange
    const importer = new OcrImporter();

    const imagePath = `data/${page}.png`;
    const byzxPath = `data/${page}.byzx`;
    const outputPathYaml = `data/${page}.actual.yaml`;
    //const outputPathByzx = `data/${page}.actual.byzx`;

    const expectedScore = SaveService.LoadScoreFromJson(
      JSON.parse(await fs.readFile(byzxPath, 'utf8')),
    );

    const expected = extractQuantitativeNeumes(expectedScore.staff.elements);

    const expectedNoteElements = expectedScore.staff.elements.filter(
      (x) => x.elementType === ElementType.Note,
    ) as NoteElement[];

    for (let i = 0; i < expectedScore.staff.elements.length; i++) {
      expectedScore.staff.elements[i].index = i;
    }

    // Act
    if (!skipOcr || !fileExists(outputPathYaml))
      await launchOcr('../scripts/do_ocr.py', imagePath, outputPathYaml);

    const elements = importer.import(await fs.readFile(outputPathYaml, 'utf8'));

    for (let i = 0; i < elements.length; i++) {
      elements[i].index = i;
    }

    const actual = extractQuantitativeNeumes(elements);

    const distance = levenshteinDistance(expected, actual);

    const similarity =
      1 - distance.distance / Math.max(expected.length, actual.length);

    const actualNoteElements = elements.filter(
      (x) => x.elementType === ElementType.Note,
    ) as NoteElement[];

    const alignment = backtrackAlignment(
      expectedNoteElements,
      actualNoteElements,
      distance.matrix,
    );

    const scorecard = calculateScorecard(
      alignment.alignedA,
      alignment.alignedB,
    );

    // Log for reporting
    report.push({
      testName: expect.getState().currentTestName!,
      page,
      similarity,
      levenshteinDistance: distance.distance,
      scorecard,
    });

    // Assert
    expect(similarity).toBeGreaterThanOrEqual(levenshteinDistanceThreshold);
  },
  timeoutInMs,
);
