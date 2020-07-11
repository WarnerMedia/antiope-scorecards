import React, { useEffect, useState } from 'react';
import Paper from '@material-ui/core/Paper';
import { getAccountsSummary } from "../../redux/middleware";
import { accountsFormatter } from './formatting'
import { useDispatch, useSelector } from "react-redux";
import dataSlice from "../../redux/reducers";
import FilterBar from "../filter/FilterBar";
import { Cache } from 'aws-amplify';
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import { useHistory } from 'react-router-dom';
import CircularProgress from '@material-ui/core/CircularProgress';
import filtering from '../../utils/filtering';
import Table from './AccountsTable';

const styles = makeStyles(stylesheet);

function getIds(accountList) {
    let ids = [];
    accountList.forEach(item => {
        ids.push(item.accountId);
    })

    return ids;
}

const Welcome = () => {
    const classes = styles();
    const data = useSelector(state => state.data.summary);
    const history = useHistory();
    const dispatch = useDispatch();
    const status = Cache.getItem("status");
    const [filtered, setFilter] = useState({});

    let rowData;
    function cellSelect(data) {
        rowData = data;
    }

    function rowSelect(column, row) {

        if (rowData && row) {
            let accountId = row.accountId;
            if (rowData.idx < 2) {
                history.push(`/ncr?accountId=${accountId}`);
            }
        }
    }

	useEffect(() => {
        let accountIds = [];
        const newStatus = Cache.getItem("status");
        if (newStatus.accountList) {
            accountIds = getIds(newStatus.accountList);
        }
        dispatch(getAccountsSummary(accountIds));
        dispatch(dataSlice.actions.setIndex(0));
    }, [dispatch]);

    const runFilter = (filtered) => {
        setFilter(filtered);
    }


	if (data) {
        let formatted = accountsFormatter(status, filtering(filtered, data));
        dispatch(dataSlice.actions.setAccounts(formatted));

        return (
            <div className={classes.exclusionsContent}>
                {status.isAdmin && <FilterBar
                                    showPayerDropdown={true}
                                    spreadsheetUrl={status.spreadsheetUrl}
                                    showPaginator={false}
                                    filter={formatted.filter}
                                    runFilter={runFilter}/>}
                    <Table cellSelect={cellSelect} rowSelect={rowSelect} {...formatted}/>
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

export default Welcome;
