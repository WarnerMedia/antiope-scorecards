import React, { useEffect, useState } from 'react';
import Paper from '@material-ui/core/Paper';
import { getNCRs, putExclusionsUser, postRemediation, getStatus } from "../../redux/middleware";
import { ncrFormatter } from './formatting'
import { useDispatch, useSelector } from "react-redux";
import { unwrapResult } from '@reduxjs/toolkit';
import { makeStyles } from '@material-ui/core/styles';
import dataSlice from "../../redux/reducers";
import FormBuilder from "../../utils/FormBuilder";
import CircularProgress from '@material-ui/core/CircularProgress';
import { Cache } from 'aws-amplify';
import stylesheet from '../styles';
import Table from './NCRTable';
import querystring from 'querystring';


const styles = makeStyles(stylesheet);

function getAllIds(accountList) {
    return accountList.map(item => item.accountId);
}

function parseLocation(search) {
    const parsed = querystring.decode(search.replace('?', ''));
    return parsed;
}

const NCR = (props) => {
    const classes = styles();
    let tags = useSelector(state => state.data.tags);
    let ncrRecords = useSelector(state => state.data.ncrRecords);

    const status = Cache.getItem("status");
    const [modalError, setError] = useState({set: false, message: ""});
    const [iacOverride, setOverride] = useState(false);
    const dispatch = useDispatch();

    useEffect(() => {
        dispatch(dataSlice.actions.setIndex(2));
        dispatch(getStatus());

        const newStatus = Cache.getItem("status");
        if (!props.location.search || props.location.search === "") {
            dispatch(getNCRs({ accountId: getAllIds(newStatus.accountList) }));
        } else {
            const accountIds = parseLocation(props.location.search);
            dispatch(getNCRs(accountIds));
        }

    }, [dispatch, props.location.search ]);

    const handleSubmit = (form) => {
        if (form.state === "remediate") {
            let body = {ncrId: form.id, remediationParameters: form.form};
            if (form.checked) {
                body.overrideIacWarning = true;
            }

            dispatch(postRemediation(body))
            .then(unwrapResult)
            .then(result => {
                if (result instanceof Error) {
                    setError({set: true, message: result.response.data.message});
                } else {
                    if (result.status && result.status === "iacOverrideRequired") {
                        setOverride(true);
                    } else if (result.status && result.status === "error") {
                        setError({set: true, message: result.message});
                    } else {
                        if (!props.location.search || props.location.search === "") {
                            dispatch(getNCRs({ accountId: getAllIds(status.accountList) }));
                        } else {
                            const accountIds = parseLocation(props.location.search);
                            dispatch(getNCRs(accountIds));
                        }
                        setOverride(false);
                        dispatch(dataSlice.actions.closed());
                    }
                }
            })
            .catch(error => {
                console.log(error);
            });
        } else {
            let fields = {
                status: form.state,
                expirationDate: form.form.expirationDate,
            };

            delete form.form["expirationDate"];
            fields.formFields = form.form;
            dispatch(putExclusionsUser({ncrId: form.id, exclusion: fields}))
            .then(unwrapResult)
            .then(result => {
                if (result instanceof Error) {
                    setError({set: true, message: result.response.data.message});
                } else {
                    if (!props.location.search || props.location.search === "") {
                        dispatch(getNCRs({ accountId: getAllIds(status.accountList) }));
                    } else {
                        const accountIds = parseLocation(props.location.search);
                        dispatch(getNCRs(accountIds));
                    }
                    dispatch(dataSlice.actions.closed());
                }
            })
            .catch(error => {
                console.log(error);
            });
        }

    };

    const onClose = () => {
        dispatch(dataSlice.actions.closed());
        setError({set: false, message: ""});
        setOverride(false);
    }

	if (ncrRecords) {
        let formatted = ncrFormatter(status, ncrRecords, tags);
        dispatch(dataSlice.actions.setNCR(formatted));

        return (
            <div className={classes.ncrContent}>
                <Table />
                <FormBuilder iacOverride={iacOverride} onClose={onClose} error={modalError} handleSubmit={handleSubmit} />
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

export default NCR;
