import React, { useState } from 'react';
import ReactDataGrid from 'react-data-grid';
import Toolbar from './Toolbar';
import { Data } from "react-data-grid-addons";


const selectors = Data.Selectors;

const sortRows = (initialRows, sortColumn, sortDirection) => rows => {
    const comparer = (a, b) => {
      if (sortDirection === "ASC") {
        return a[sortColumn] > b[sortColumn] ? 1 : -1;
      } else if (sortDirection === "DESC") {
        return a[sortColumn] < b[sortColumn] ? 1 : -1;
      }
    };
    return sortDirection === "NONE" ? initialRows : [...rows].sort(comparer);
  };

const handleFilterChange = filter => filters => {
    const newFilters = { ...filters };
    if (filter.filterTerm) {
        newFilters[filter.column.key] = filter;
    } else {
        delete newFilters[filter.column.key];
    }
    return newFilters;
};

function getValidFilterValues(rows, columnId) {
    return rows
      .map(r => r[columnId])
      .filter((item, i, a) => {
        return i === a.indexOf(item);
      });
}

function getRows(rows, filters) {
    return selectors.getRows({ rows, filters });
}

const Table = ({ rows, columns, cellSelect, rowSelect }) => {
    const [filters, setFilters] = useState({});
    const [definedRows, setRows] = useState(rows);

    let filteredRows = getRows(definedRows, filters);

    function rSelect() {

    }

    function cSelect() {

    }

    if (!cellSelect) {
      cellSelect = cSelect;
    }

    if (!rowSelect) {
      rowSelect = rSelect;
    }

        return (
            <ReactDataGrid
                columns={columns}
                rowGetter={i => filteredRows[i]}
                rowsCount={filteredRows.length}
                onCellSelected={cellSelect}
                onRowClick={rowSelect}
                toolbar={<Toolbar enableFilter={true} />}
                onAddFilter={filter => setFilters(handleFilterChange(filter))}
                onClearFilters={() => setFilters({})}
                getValidFilterValues={columnKey => getValidFilterValues(definedRows, columnKey)}
                onGridSort={(sortColumn, sortDirection) =>
                    setRows(sortRows(rows, sortColumn, sortDirection))
                }
            />
        )


}

export default Table;
