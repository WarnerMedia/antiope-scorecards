import React, { useState } from 'react';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import ListItemText from '@material-ui/core/ListItemText';
import Select from '@material-ui/core/Select';
import { Cache } from 'aws-amplify';
import { putExclusions, getExclusions } from "../../redux/middleware";
import { makeStyles } from '@material-ui/core/styles';
import dataSlice from "../../redux/reducers.js";
import stylesheet from '../styles';
import { unwrapResult } from '@reduxjs/toolkit';
import { useDispatch } from "react-redux";
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Checkbox from '@material-ui/core/Checkbox';

const styles = makeStyles(stylesheet);

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const AddExclusionModal = function(props) {
    const classes = styles();
    const dispatch = useDispatch();
    const [form, setForm] = useState({});
    const [accountId, setAccountId] = useState("");
    const [accountIdError, setAccountIdError] = useState(false);
    const [checked, setChecked] = useState(false);
    const [resourceId, setResourceId] = useState("");
    const [expirationDate, setExpirationDate] = useState("");
    const [textFields, setFields] = useState([]);
    const [requirementId, setRequirementId] = useState("");
    let { exclusionTypes, requirements } = Cache.getItem("status");

    requirements = requirements.sort((a, b) => a.requirementId.localeCompare(b.requirementId));

    const handleChange = (event) => {
        setForm({ ...form, [event.target.id]: event.target.value});
    };

    const handleAccountIdChange = (event) => {
        let val = event.target.value;
        setAccountId(val);
        if (val.length === 12 || val === "*" || val.length === 0) {
            setAccountIdError(false);
        } else {
            setAccountIdError(true);
        }
    }

    const handleResourceIdChange = (event) => {
        setResourceId(event.target.value);
    }
    const handleExpirationDateChange = (event) => {
        setExpirationDate(event.target.value);
    }

    const handleCreateExclusion = () => {
        let fields = {
            accountId: accountId,
            resourceId: resourceId,
            status: "initial",
            expirationDate: expirationDate,
            formFields: form,
            requirementId: requirementId,
            hidesResources: checked
        };

        dispatch(putExclusions({exclusion: fields}))
        .then(unwrapResult)
        .then(result => {
            if (result instanceof Error) {
                console.log(result.response.data);
            } else {
                dispatch(getExclusions());
                dispatch(dataSlice.actions.exclusionClosed());
            }
        })
        .catch(error => {
            console.log(error);
        });
    }

    const handleClose = () => {
        setForm({});
        setRequirementId("");
        setChecked(false);
        dispatch(dataSlice.actions.exclusionClosed());
    };

    const handleCheckbox = (event) => {
        setChecked(event.target.checked);
    };

    const handleSelectorChange = (event) => {
        let reqId = event.target.value
        setRequirementId(reqId);
        setForm({ ...form, requirementId: reqId});
        let finalFields = [];

        requirements.forEach(item => {
            if (item.requirementId === reqId) {
                let formFields = exclusionTypes[item.exclusionType].formFields;
                Object.keys(formFields).forEach(key => {
                    let field = formFields[key];
                    let form = createField(
                        {
                            label: field.label,
                            placeholder: field.placeholder,
                            id: key
                        }
                    );

                    finalFields.push(form);
                });
            }
        })

        setFields(finalFields);

    }

    function createField(item) {
        return (
                <TextField
                    margin="dense"
                    onChange={handleChange}
                    id={item.id}
                    key={item.id}
                    label={item.label}
                    helperText={item.placeholder}
                    type="email"
                    fullWidth
                />
        );
    }

    if (props.open) {
        return (
            <div>
                <Dialog open={props.open} onClose={handleClose} aria-labelledby="form-dialog-title">
                        <DialogTitle id="form-dialog-title">Add Exclusion</DialogTitle>
                        <DialogContent>
                            <TextField
                                margin="dense"
                                onChange={handleAccountIdChange}
                                id="accountId"
                                label="Account Id"
                                type="email"
                                error={accountIdError}
                                fullWidth
                            />
                            <TextField
                                margin="dense"
                                onChange={handleResourceIdChange}
                                id="resourceId"
                                label="Resource Id"
                                type="email"
                                fullWidth
                            />
                            <TextField
                                margin="dense"
                                onChange={handleExpirationDateChange}
                                id="resourceId"
                                placeholder="yyyy/mm/dd"
                                label="Expiration Date"
                                type="email"
                                fullWidth
                            />
                                <FormControl className={classes.formControl}>
                                    <InputLabel id="checkbox-label">Requirement Id</InputLabel>
                                    <Select
                                        labelId="checkbox-label"
                                        id="checkbox"
                                        value={requirementId}
                                        name="payers"
                                        onChange={handleSelectorChange}
                                        MenuProps={MenuProps}
                                    >
                                    {requirements.map((req) => (
                                        <MenuItem name={req.exclusionType} key={req.requirementId} value={req.requirementId}>
                                            <ListItemText primary={req.requirementId} />
                                        </MenuItem>
                                    ))}
                                    </Select>
                                </FormControl>
                                {textFields}
                                <div>
                                    <FormControlLabel
                                    control={<Checkbox checked={checked} onChange={handleCheckbox} name="checkBox" />}
                                    label="Resource is Hidden"
                                    />
                                </div>
                         </DialogContent>
                        <DialogActions>
                            <Button onClick={handleClose} color="primary">
                                Cancel
                            </Button>
                            <Button onClick={handleCreateExclusion} color="primary">
                                Add
                            </Button>
                        </DialogActions>
                    </Dialog>
            </div>
        );
    } else {
        return (<div></div>);
    }

}

export default AddExclusionModal;
