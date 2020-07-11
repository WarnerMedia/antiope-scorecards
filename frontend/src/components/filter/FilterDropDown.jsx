import React from 'react';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import ListItemText from '@material-ui/core/ListItemText';
import Select from '@material-ui/core/Select';
import Checkbox from '@material-ui/core/Checkbox';
import IconButton from '@material-ui/core/IconButton';
import CloseIcon from '@material-ui/icons/Close';

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

const PayersFilter = (props) => {

    if (!props.filter) {
        return <div></div>
    } else {
        return (
            <div className={props.classes.chips}>
                    <FormControl className={props.classes.formControl}>
                        <InputLabel id="demo-mutiple-checkbox-label">Payers</InputLabel>
                        <Select
                        labelId="demo-mutiple-checkbox-label"
                        id="demo-mutiple-checkbox"
                        multiple
                        value={props.payerName}
                        name="payers"
                        onChange={props.handleChange}
                        input={<Input />}
                        renderValue={(selected) =>
                        {
                            let display = [];

                            selected.forEach(item => {
                                display.push(item);
                            });

                            return display.join(', ')
                        }}
                        MenuProps={MenuProps}
                        >
                        {props.accountList.map((payer) => (
                            <MenuItem key={payer.accountId} value={payer.accountName}>
                                <Checkbox checked={props.payerName.indexOf(payer.accountName) > -1} />
                                <ListItemText primary={payer.accountName} />
                            </MenuItem>
                        ))}
                        </Select>
                    </FormControl>
                    <IconButton onClick={props.clearDropdowns} aria-label="clear" size="small">
                        <CloseIcon fontSize="inherit" />
                    </IconButton>
            </div>

        )
    }

 }



 export default PayersFilter;
