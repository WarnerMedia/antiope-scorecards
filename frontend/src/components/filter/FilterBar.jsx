import React from 'react';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import FilterDropDown from './FilterDropDown';
// import { InputBase } from '@material-ui/core';
// import SearchIcon from '@material-ui/icons/Search';
import { Cache } from 'aws-amplify';
import TablePagination from '@material-ui/core/TablePagination';


import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import { useEffect, useState } from 'react';
const styles = makeStyles(stylesheet);

const getAccountIds = function(ids, payers) {
    let accountIds = [];
    ids.forEach(id => {
        payers.forEach(payer => {
            if (payer.accountName === id) {
                accountIds = accountIds.concat(payer.accountList);
            }
        })
    })

    return accountIds;
}

function formatAccounts(accountList) {
    let accounts = []
    accountList.forEach(item => {
        accounts.push({accountId: item.id, accountName: item.accountName});
    });

    return accounts;
}


export const FilterBar = (props) => {
    const classes = styles();
    const propsFilter = props.filter ? props.filter : {};
    const [payerName, setPayerName] = useState([]);
    const [search, setSearch] = useState("");

    const [otherFilter, setOtherFilter] = useState({});
    const { payerAccounts } = Cache.getItem('status');
    const accountList = formatAccounts(payerAccounts);
    const {runFilter} = props;

    const handleChange = (event) => {
        if (event.target.name === 'search') {
            setSearch(event.target.value);
        } else if (event.target.name === 'payers') {
            setPayerName(event.target.value);
            let accountIds = getAccountIds(event.target.value, payerAccounts);
            runFilter({
                search: search,
                payers: accountIds,
                other: otherFilter
            })
        } else {
            const filters = { ...otherFilter };
            filters[event.target.name] = event.target.value;
            setOtherFilter(filters);
        }

    };

    const handleChangePage = (event, newPage) => {
        props.changePaginatedData(newPage);
    };

    const clearDropdowns = () => {
        setPayerName([]);
        setOtherFilter({});
    }

    useEffect(() => {

    }, [search, payerName, otherFilter, propsFilter.payers]);

    return (
        <Paper className={classes.filterBar}>
            <Grid
            container
            direction="row"
            justify="center"
            alignItems="center">
                <Grid
                container
                item
                direction="row"
                justify="flex-start"
                alignItems="flex-start"
                xs={4}>
                    {props.showPaginator &&
                    <TablePagination
                    component="div"
                    count={props.paginationLength}
                    rowsPerPage={props.rowsPerPage}
                    rowsPerPageOptions={[100]}
                    page={props.page}
                    onChangePage={handleChangePage}
                    />
                    }

                    {props.spreadsheetUrl &&
                        <a className={classes.spreadsheetLink} target="_blank" rel="noopener noreferrer" href={props.spreadsheetUrl}>My Spreadsheet</a>
                    }

                    {/* <div className={classes.search}>
                        <div className={classes.searchIcon}>
                            <SearchIcon />
                        </div>
                            <InputBase
                                placeholder="Search…"
                                classes={{
                                    root: classes.inputRoot,
                                    input: classes.inputInput,
                                }}
                                name="search"
                                onChange={handleChange}
                                inputProps={{ 'aria-label': 'search' }}
                            />
                    </div> */}

                </Grid>
                <Grid
                container
                item
                direction="row"
                justify="flex-end"
                alignItems="flex-end"
                xs={8}>
                    {props.showPayerDropdown &&
                        <FilterDropDown
                        payerName={payerName}
                        clearDropdowns={clearDropdowns}
                        handleChange={handleChange}
                        accountList={accountList}
                        classes={classes}
                        filter={props.filter} />
                    }

                </Grid>
            </Grid>
        </Paper>

    )
}

export default FilterBar;
