import { useDispatch, useSelector } from "react-redux";
import React, {useEffect} from 'react';
import dataSlice from "../../redux/reducers";
import Paper from "@material-ui/core/Paper";
import CircularProgress from "@material-ui/core/CircularProgress";
import {makeStyles} from "@material-ui/core/styles";
import stylesheet from "../styles";
import {getScans} from "../../redux/middleware";

const styles = makeStyles(stylesheet);

const ScansView = (props) => {
    const classes = styles();
    let data = useSelector(state => state.data.scansRecords);

    const dispatch = useDispatch();

    useEffect(() => {
        dispatch(dataSlice.actions.setIndex(4));
        dispatch(getScans());
    }, [dispatch]);

    if (data) {
        let toRender = {};
        let i;
        let targetId = decodeURIComponent(props.match.params.scanId);
        for (i in data) {
            if (data[i].scanId && data[i].scanId === targetId) {
                toRender = data[i];
                break;
            }
        }
        return (
            <pre className={classes.scanView}>{JSON.stringify(toRender, null, 2) }</pre>
        );
    } else {
        return (
            <Paper className={classes.loadingContent}>
                <CircularProgress size={48} />
            </Paper>
        );
    }
}

export default ScansView;
