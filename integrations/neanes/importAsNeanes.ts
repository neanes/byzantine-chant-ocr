import { promises as fs } from 'fs';
import { Score } from './neanes/models/Score';
import { EmptyElement } from './neanes/models/Element';
import { SaveService } from './neanes/services/SaveService';
import { OcrImporter } from './OcrImporter';

const importer = new OcrImporter();

// Blank score
const score = new Score();

const elements = importer.import(await fs.readFile('output.yaml', 'utf8'));

// Remove the empty element
score.staff.elements.pop();

elements.forEach((x) => score.staff.elements.push(x));

// Final element
score.staff.elements.push(new EmptyElement());

await fs.writeFile(
  'output.byzx',
  JSON.stringify(SaveService.SaveScoreToJson(score)),
);
