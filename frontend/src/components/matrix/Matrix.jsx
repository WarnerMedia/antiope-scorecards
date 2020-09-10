import React, { useEffect, useState } from 'react';
import Paper from '@material-ui/core/Paper';
import { getAccountsScore, getStatus } from "../../redux/middleware";
import { matrixFormatter } from './formatting'
import { useDispatch, useSelector } from "react-redux";
import FilterBar from "../filter/FilterBar";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import { useHistory } from 'react-router-dom';
import { Cache } from 'aws-amplify';

import filtering from '../../utils/filtering';
import CircularProgress from '@material-ui/core/CircularProgress';
import dataSlice from "../../redux/reducers";
import MatrixTable from './MatrixTable';


const styles = makeStyles(stylesheet);

function getIds(accountList) {
    let ids = [];
    let i;
    for (i = 0; i < accountList.length; i++) {
        let item = accountList[i];
        ids.push(item.accountId);
    }
    // accountList.forEach(item => {
    //     ids.push(item.accountId);
    // })

    return ids;
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

function getAllIds(accountList) {
    return accountList.map(account => account.accountId);
}

const Matrix = () => {
    const history = useHistory();
    const classes = styles();
    const [page, setPage] = React.useState(0);
    const dispatch = useDispatch();
    const [filtered, setFilter] = useState({});
    const status = Cache.getItem("status");

    let showPaginator = false;
    let data = useSelector(state => state.data.accounts);
    let dataLength = 0;
    let showFilterBar = false;
    let showPayerDropdown = true;

    if (status.isAdmin) {
        showFilterBar = true;
    } else {
        showPayerDropdown = false;
    }

    const changePaginatedData = (newPage) => {
        setPage(newPage);
    }

    let rowData;

    function cellSelect(data) {
        rowData = data;
    }

    function rowSelect(column, row) {
        if (rowData && row) {
            let requirementId = JSON.parse(row.requirementId).value;
            if (rowData.idx < 3) {
                const accountIdQuerystring = getAllIds(status.accountList).map(accountId => `accountId=${accountId}`).join('&');
                history.push(`/ncr?${accountIdQuerystring}&requirementId=${requirementId}`);
            } else if (rowData.idx >= 3) {
                let idKeys = Object.keys(row);
                history.push(`/ncr?requirementId=${requirementId}&accountId=${idKeys[rowData.idx]}`);
            }
        }
    }

	useEffect(() => {
        dispatch(dataSlice.actions.setIndex(1));
        dispatch(getStatus());
        let accountIds = [];
        const newStatus = Cache.getItem("status");
        if (newStatus.accountList) {
            accountIds = getIds(newStatus.accountList);
        }
        dispatch(getAccountsScore(accountIds));
    }, [dispatch]);

    const runFilter = (filtered) => {
        setFilter(filtered);
    }

	if (status && data) {
        let filteredData = filtering(filtered, data);

        if (filteredData.length > 100) {
            showPaginator = true;
            showFilterBar = true;

            dataLength = filteredData.length;
            if (page === 0) {
                filteredData = getPaginatedData({lesser: 0, greater: 100}, filteredData);
            } else {
                filteredData = getPaginatedData({lesser: (page * 100), greater: ((page + 1) * 100)}, filteredData);
            }
        }

        let formatted = matrixFormatter(status, filteredData);

        dispatch(dataSlice.actions.setMatrix(formatted));

        return (
            <div className={classes.exclusionsContent}>
                {showFilterBar &&
                <FilterBar
                showPaginator={showPaginator}
                rowsPerPage={100}
                showPayerDropdown={showPayerDropdown}
                paginationLength={dataLength}
                page={page}
                changePaginatedData={changePaginatedData}
                filter={formatted.filter}
                runFilter={runFilter}/>}
                <MatrixTable cellSelect={cellSelect} rowSelect={rowSelect} />
            </div>

        );
    } else {
        return (
            <Paper className={classes.loadingContent}>
                <CircularProgress size={48} />
            </Paper>
        );
    }

}

export default Matrix;
