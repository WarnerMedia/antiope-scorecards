import React, { useState } from 'react';
import ReactDataGrid from 'react-data-grid';
import Toolbar from '../../utils/Toolbar';
import { Data } from "react-data-grid-addons";
import { useDispatch, useSelector } from "react-redux";
import dataSlice from "../../redux/reducers";


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
    let t = new Set(rows
        .map(r => r[columnId]));

    return Array.from(t);
}

function getRows(rows, filters) {
    return selectors.getRows({ rows, filters });
}

const Table = () => {
    const [filters, setFilters] = useState({});
    const dispatch = useDispatch();
    let data = useSelector(state => state.data.accountsFormatted);

    let filteredRows = getRows(data.rows, filters);

        return (
            <ReactDataGrid
                columns={data.columns}
                rowGetter={i => filteredRows[i]}
                rowsCount={filteredRows.length}
                toolbar={<Toolbar enableFilter={true} />}
                onAddFilter={filter => setFilters(handleFilterChange(filter))}
                onClearFilters={() => setFilters({})}
                getValidFilterValues={columnKey => getValidFilterValues(data.rows, columnKey)}
                onGridSort={(sortColumn, sortDirection) => {
                    let _data = {...data}
                    let sorted = sortRows(data.rows, sortColumn, sortDirection)(data.rows);
                    _data.rows = sorted;
                    dispatch(dataSlice.actions.setAccounts(_data));
                }

                }
            />
        )


}

export default Table;
