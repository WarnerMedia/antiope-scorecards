import React, { useState, useEffect } from 'react';
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
import { useSelector } from "react-redux";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../components/styles';
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

const FormBuilder = function(props) {
    const modalOpen = useSelector(state => state.data.modalOpen);
    const classes = styles();
    const [form, setForm] = useState({});
    const [state, setState] = useState("");
    const [hidesResources, setHidesResources] = useState(modalOpen.formData.isHidden);

    const [checked, setChecked] = useState(false);

    const handleChange = (event) => {
        setForm({ ...form, [event.target.id]: event.target.value});
    };

    const handleCheckbox = (event) => {
        setChecked(event.target.checked);
    };

    const handleResourcesCheckbox = (event) => {
        setHidesResources(event.target.checked);
    };

    const handleClose = () => {
        setForm({});
        setState("");
        props.onClose();
    };

    const handleSelectorChange = (event) => {
        let state = event.target.value
        setState(state);
    }

    useEffect(() => {
        setHidesResources(modalOpen.formData.isHidden);
    }, [modalOpen.formData.isHidden]);

    let textFields = [];
    let actions = [];

    function createLabel(item) {
        return (
                <div>
                    <span>{item.label}: </span>
                    <span>{item.value}</span>
                </div>
        );
    }

    function createField(item) {
        return (
                <TextField
                    margin="dense"
                    onChange={handleChange}
                    id={item.id}
                    error={props.error.set}
                    label={item.label}
                    helperText={item.placeholder}
                    defaultValue={item.default}
                    type="email"
                    fullWidth
                />
        );
    }

    function createAction(item, id, type) {
        return (
            <Button
                onClick={() => {props.handleSubmit({id: id,
                                    state: item.id,
                                    newState: state,
                                    hidesResources: hidesResources,
                                    checked: checked,
                                    form: form,
                                    type: type})}}
                color="primary">
                {item.title}
            </Button>
        )
    }

    if (modalOpen.formData.fields) {
        modalOpen.formData.fields.forEach(item => {
            if (item.type === "label") {
                textFields.push(createLabel(item));
            } else if (item.type === "field") {
                textFields.push(createField(item));
            }
        });

        modalOpen.formData.modalActions.forEach(item => {
            actions.push(createAction(item, modalOpen.formData.id, modalOpen.formData.type));
        });

        return (
            <div>
                <Dialog fullWidth={true} maxWidth="md" open={modalOpen.isOpen} onClose={handleClose} aria-labelledby="form-dialog-title">
                        <DialogTitle id="form-dialog-title">{modalOpen.formData.display}</DialogTitle>
                        <DialogContent>
                            {textFields}
                            {modalOpen.formData.dropdown &&
                                <FormControl className={classes.formControl}>
                                    <InputLabel id="checkbox-label">State</InputLabel>
                                    <Select
                                        labelId="checkbox-label"
                                        id="checkbox"
                                        value={state}
                                        name="payers"
                                        error={props.error.set}
                                        onChange={handleSelectorChange}
                                        MenuProps={MenuProps}
                                    >
                                    {modalOpen.formData.dropdown.map((state) => (
                                        <MenuItem name={state.state} key={state.state} value={state.state}>
                                            <ListItemText primary={state.state} />
                                        </MenuItem>
                                    ))}
                                    </Select>
                                </FormControl>
                            }

                            {props.iacOverride &&
                                <div>
                                    <FormControlLabel
                                    control={<Checkbox checked={checked} onChange={handleCheckbox} name="checkBox" />}
                                    label="Request Iac Override"
                                    />
                                </div>
                            }

                            {props.isExclusion &&
                                <div>
                                    <FormControlLabel
                                    control={<Checkbox checked={hidesResources} onChange={handleResourcesCheckbox} name="checkBox" />}
                                    label="Resource is Hidden"
                                    />
                                </div>
                            }

                            {props.error.set &&
                                <span className={classes.modalError}>{props.error.message}</span>}
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleClose} color="primary">
                                Cancel
                            </Button>
                            {actions}
                        </DialogActions>
                    </Dialog>
            </div>
        );
    } else {
        return (<div></div>);
    }



}

export default FormBuilder;
