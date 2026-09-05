// Existing small export; wire into the existing scheduler after requirements review.
export function toCsv(rows) {
  return 'id,total\n' + rows.map(row => `${row.id},${row.total}`).join('\n') + '\n';
}
