import React, { useEffect } from 'react';
import Paper from '@material-ui/core/Paper';
import {getScans} from "../../redux/middleware";
import { scansFormatter } from './formatting'
import { useDispatch, useSelector } from "react-redux";
import { makeStyles } from '@material-ui/core/styles';
import dataSlice from "../../redux/reducers";
import CircularProgress from '@material-ui/core/CircularProgress';
import stylesheet from '../styles';
import Table from './ScansTable';


const styles = makeStyles(stylesheet);


const Scans = (props) => {
    const classes = styles();
    let scansRecords = useSelector(state => state.data.scansRecords);

    const dispatch = useDispatch();

    useEffect(() => {
        dispatch(dataSlice.actions.setIndex(4));
        dispatch(getScans());

    }, [dispatch]);


	if (scansRecords) {
        let formatted = scansFormatter(scansRecords);
        dispatch(dataSlice.actions.setScans(formatted));

        return (
            <div className={classes.ncrContent}>
                <Table />
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

export default Scans;
