import {
  ElementType,
  NoteElement,
  ScoreElement,
} from '../../integrations/neanes/neanes/models/Element';

export function extractQuantitativeNeumes(elements: ScoreElement[]) {
  const results: string[] = [];
  for (const e of elements) {
    if (e.elementType === ElementType.Note) {
      results.push((e as NoteElement).quantitativeNeume);
    }
  }

  return results;
}

// _editor.elements.filter(x => x.elementType === 'Note').map(x => x.quantitativeNeume);
