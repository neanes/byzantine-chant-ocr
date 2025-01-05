export function levenshteinDistance(a: string[], b: string[]): number {
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

  return d[m][n];
}
