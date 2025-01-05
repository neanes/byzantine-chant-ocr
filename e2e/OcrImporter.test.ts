import { promises as fs } from 'fs';
import { afterAll, expect, test } from '@jest/globals';

import { OcrImporter } from '../integrations/neanes/OcrImporter';
import { extractQuantitativeNeumes } from './util/extractQuantitativeNeumes';
import { launchOcr } from './util/launchOcr';
import { levenshteinDistance } from './util/levenshtein';
import { SaveService } from '../integrations/neanes/neanes/services/SaveService';

const levenshteinDistanceThreshold = 0.9;
const timeoutInMs = 120 * 1000;
const reportFilePath = 'OcrImporter.report.json';
const report: Array<{
  testName: string;
  page: string;
  levenshteinDistance: number;
  similarity: number;
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

    const expectedScore = SaveService.LoadScoreFromJson(
      JSON.parse(await fs.readFile(byzxPath, 'utf8')),
    );

    const expected = extractQuantitativeNeumes(expectedScore.staff.elements);

    // Act
    const elements = importer.import(
      await launchOcr('../scripts/do_ocr.py', imagePath),
    );

    const actual = extractQuantitativeNeumes(elements);

    const distance = levenshteinDistance(expected, actual);

    const similarity = 1 - distance / Math.max(expected.length, actual.length);

    // Log for reporting
    report.push({
      testName: expect.getState().currentTestName!,
      page,
      similarity,
      levenshteinDistance: distance,
    });

    // Assert
    expect(similarity).toBeGreaterThanOrEqual(levenshteinDistanceThreshold);
  },
  timeoutInMs,
);
