// import { jsonObjectCells } from './init.js';

// Функция для поиска ячейки по ID
export function searchCellById(CellId) {
  let jsonObjectCells = window.appData.сells;
    //console.log("Функция searchCellById инициализирована")
  for (const rowKey in jsonObjectCells.rows) {
    const row = jsonObjectCells.rows[rowKey];
    for (const cellKey in row.cells) {
      const cell = row.cells[cellKey];
      if (cell.id == CellId) {
        //console.log(cell)
        return cell;
      }
    }
  }
  return null;  // Если ячейка не найдена
}