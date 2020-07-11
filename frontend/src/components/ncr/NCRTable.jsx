import React, { useState } from 'react';
import ReactDataGrid from 'react-data-grid';
import Toolbar from '../../utils/Toolbar';
import { Data } from "react-data-grid-addons";
import { useDispatch, useSelector } from "react-redux";
import dataSlice from "../../redux/reducers";
import FilterBar from "../filter/FilterBar";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';


const styles = makeStyles(stylesheet);
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


function getValidFilterValues(rows, columnId) {
    let t = new Set(rows
        .map(r => r[columnId]));

    return Array.from(t);
}

function getPaginatedData(page, data) {
    let newData = [];

    data.forEach((item, index) => {
        if (index >= page.lesser && index <= page.greater) {
            newData.push(item);
        }
    })

    return newData;
}

function getRows(rows, filters) {
    return selectors.getRows({ rows, filters });
}

const Table = () => {
    const [filters, setFilters] = useState({});
    const classes = styles();

    const dispatch = useDispatch();
    let data = useSelector(state => state.data.ncrFormatted);
    const [page, setPage] = React.useState(0);

    let filteredRows = getRows(data.rows, filters);
    let rowLength = filteredRows.length;

    if (filteredRows.length > 1000) {
        if (page === 0) {
            filteredRows = getPaginatedData({lesser: 0, greater: 1000}, filteredRows);
        } else {
            filteredRows = getPaginatedData({lesser: (page * 1000), greater: ((page + 1) * 1000)}, filteredRows);
        }
    }

    const changePaginatedData = (newPage) => {
        setPage(newPage);
    }

    const handleFilterChange = filter => filters => {
        changePaginatedData(0);
        const newFilters = { ...filters };
        if (filter.filterTerm) {
            newFilters[filter.column.key] = filter;
        } else {
            delete newFilters[filter.column.key];
        }
        return newFilters;
    };

    return (
        <div className={classes.exclusionsContent}>
            <FilterBar
                showPaginator={true}
                rowsPerPage={1000}
                showPayerDropdown={false}
                paginationLength={rowLength}
                page={page}
                changePaginatedData={changePaginatedData}
                />
            <ReactDataGrid
                columns={data.columns}
                rowGetter={i => filteredRows[i]}
                rowsCount={filteredRows.length}
                toolbar={<Toolbar enableFilter={true} />}
                onAddFilter={filter => setFilters(handleFilterChange(filter))}
                onClearFilters={() => setFilters({})}
                getValidFilterValues={columnKey => getValidFilterValues(data.rows, columnKey)}
                onGridSort={(sortColumn, sortDirection) => {
                    let _data = {...data};
                    let sorted = sortRows(data.rows, sortColumn, sortDirection)(data.rows);
                    _data.rows = sorted;
                    dispatch(dataSlice.actions.setNCR(_data));
                }

                }
            />
        </div>
    )

}

export default Table;
