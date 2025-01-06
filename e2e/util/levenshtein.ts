import {
  EmptyElement,
  NoteElement,
  ScoreElement,
} from '../../integrations/neanes/neanes/models/Element';

export function levenshteinDistance(a: string[], b: string[]) {
  const m = a.length;
  const n = b.length;

  const d: number[][] = Array.from({ length: m + 1 }, () =>
    Array(n + 1).fill(0),
  );

  // Prefill deletions
  for (let i = 0; i <= m; i++) {
    d[i][0] = i;
  }

  // Prefill insertions
  for (let j = 0; j <= n; j++) {
    d[0][j] = j;
  }

  for (let j = 1; j <= n; j++) {
    for (let i = 1; i <= m; i++) {
      let substitutionCost = a[i - 1] === b[j - 1] ? 0 : 1;

      d[i][j] = Math.min(
        d[i - 1][j] + 1, // Deletion
        d[i][j - 1] + 1, // Insertion
        d[i - 1][j - 1] + substitutionCost, // Substitution
      );
    }
  }

  return { distance: d[m][n], matrix: d };
}

export function backtrackAlignment(
  a: NoteElement[],
  b: NoteElement[],
  d: number[][],
): { alignedA: ScoreElement[]; alignedB: ScoreElement[] } {
  let i = a.length;
  let j = b.length;

  let alignedA: ScoreElement[] = [];
  let alignedB: ScoreElement[] = [];

  // Start at the bottom-right corner of the matrix and trace back to the top-left
  while (i > 0 || j > 0) {
    // 1. If we're at the top row, we must have inserted all remaining characters of `b` into `a`
    if (i === 0) {
      alignedA.unshift(new EmptyElement()); // Gap in `a`
      alignedB.unshift(b[j - 1]);
      j--;
    }
    // 2. If we're at the leftmost column, we must have deleted all remaining characters of `a`
    else if (j === 0) {
      alignedA.unshift(a[i - 1]); // Character from `a`
      alignedB.unshift(new EmptyElement()); // Gap in `b`
      i--;
    }
    // 3. Check if the current cell represents a match or substitution
    else if (
      d[i][j] === d[i - 1][j - 1] &&
      a[i - 1].quantitativeNeume === b[j - 1].quantitativeNeume
    ) {
      alignedA.unshift(a[i - 1]); // Matching character from `a`
      alignedB.unshift(b[j - 1]); // Matching character from `b`
      i--; // Move diagonally up-left
      j--;
    }
    // 4. Handle a substitution
    else if (d[i][j] === d[i - 1][j - 1] + 1) {
      alignedA.unshift(a[i - 1]); // Character from `a`
      alignedB.unshift(b[j - 1]); // Substituted character from `b`
      i--; // Move diagonally up-left
      j--;
    }
    // 5. Handle a deletion
    else if (d[i][j] === d[i - 1][j] + 1) {
      alignedA.unshift(a[i - 1]); // Character from `a`
      alignedB.unshift(new EmptyElement()); // Gap in `b`
      i--; // Move up
    }
    // 6. Handle an insertion
    else if (d[i][j] === d[i][j - 1] + 1) {
      alignedA.unshift(new EmptyElement()); // Gap in `a`
      alignedB.unshift(b[j - 1]); // Character from `b`
      j--; // Move left
    }
  }

  return { alignedA, alignedB };
}
