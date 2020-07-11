import React, { useEffect } from 'react';
import Paper from '@material-ui/core/Paper';

import { getExclusions, putExclusions } from "../../redux/middleware";
import { exclusionsFormatter } from './formatting';
import { useDispatch, useSelector } from "react-redux";

import Fab from '@material-ui/core/Fab';
import AddIcon from '@material-ui/icons/Add';
import { makeStyles } from '@material-ui/core/styles';
import { unwrapResult } from '@reduxjs/toolkit';
import stylesheet from '../styles';
import { useState } from 'react';
import dataSlice from "../../redux/reducers.js";
import AddExclusionModal from './AddExclusionModal';
import FormBuilder from "../../utils/FormBuilder";
import { Cache } from 'aws-amplify';
import CircularProgress from '@material-ui/core/CircularProgress';
import Table from './ExclusionsTable';

const styles = makeStyles(stylesheet);


const Exclusions = () => {
    const classes = styles();
    ///SPLIT STATE UP HERE
    const exclusions = useSelector(state => state.data.exclusions);
    const exclusionModalOpen = useSelector(state => state.data.exclusionModalOpen);

    const dispatch = useDispatch();
    const status = Cache.getItem("status");
    const [modalError, setError] = useState({set: false, message: ""});


	useEffect(() => {
        dispatch(dataSlice.actions.setIndex(3));
        dispatch(getExclusions());
    }, [dispatch]);

    const fabClick = () => {
        dispatch(dataSlice.actions.exclusionOpen());
    }

    const handleSubmit = (form) => {
        let fields = {};

        if (form.newState && form.newState.length > 0) {
            fields.status = form.newState;
        } else {
            fields.status = form.type
        }

        fields.hidesResources = form.hidesResources ? form.hidesResources : false;


        if (form.form.adminComments) {
            fields.adminComments = form.form.adminComments;
            delete form.form["adminComments"];
        }

        if (form.form.accountId) {
            fields.accountId = form.form.accountId;
            delete form.form["accountId"];
        }

        if (form.form.resourceId) {
            fields.resourceId = form.form.resourceId;
            delete form.form["resourceId"];
        }

        if (form.form.expirationDate) {
            fields.expirationDate = form.form.expirationDate
        }

        delete form.form["expirationDate"];
        fields.formFields = form.form;
        dispatch(putExclusions({exclusionId: form.id, exclusion: fields}))
        .then(unwrapResult)
        .then(result => {
            if (result instanceof Error) {
                setError({set: true, message: result.response.data.message});
            } else {
                dispatch(getExclusions());
                dispatch(dataSlice.actions.closed());
            }
        })
        .catch(error => {
            console.log(error);
        });
    };

    const onClose = () => {
        dispatch(dataSlice.actions.closed());
        setError({set: false, message: ""});
    }

	if (exclusions) {
        let formatted = exclusionsFormatter(exclusions, status);
        dispatch(dataSlice.actions.setExclusions(formatted));
        return (
            <div className={classes.exclusionsContent}>
                <AddExclusionModal open={exclusionModalOpen} />
                <Table />
                <FormBuilder isExclusion={true} onClose={onClose} error={modalError} handleSubmit={handleSubmit}/>

                <Fab onClick={fabClick} className={classes.fab} color="secondary" aria-label="add">
                    <AddIcon />
                </Fab>


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

export default Exclusions;
