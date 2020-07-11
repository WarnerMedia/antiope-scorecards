import React from 'react';
import dataSlice from "../../redux/reducers";
import { useDispatch } from "react-redux";
import { Filters } from "react-data-grid-addons";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import { EditButton, ReviewButton } from '../../utils/Buttons'

const styles = makeStyles(stylesheet);
const { MultiSelectFilter } = Filters;

const columnProps = {
    width: 160,
    resizable: true
}

const ButtonFormatter = ({value}) => {
    const dispatch = useDispatch();
    const {actions} = dataSlice;
    const classes = styles();

    if (!value) {
        return <div></div>;
    } else if (value.kind === "edit") {
        return <EditButton className={classes.tableButton} onClick={() => {dispatch(actions.open(value))}} variant='contained'>{value.action}</EditButton>
    } else if (value.kind === "review") {
        return <ReviewButton className={classes.tableButton} onClick={() => {dispatch(actions.open(value))}} variant='contained'>{value.action}</ReviewButton>
    }
}

const exclusionsFormatter = function(exclusions, status) {
    const { exclusionTypes } = status;
    let rows = [];
    let columns = [
        { key: 'accountId', name: 'Account Id', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'requirementId', name: 'Requirement Id', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'resourceId', name: 'Resource Id', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'status', name: 'Exclusion Status', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'type', name: 'Type', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'reason', name: 'Reason', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'hidesResources', name: 'Is Hidden', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'expiration', name: 'Expiration', filterRenderer: MultiSelectFilter, sortable: true, filterable: true },
        { key: 'adminComments', name: 'Comments', filterRenderer: MultiSelectFilter, filterable: true },
        { key: 'lastStatusChangeDate', name: 'Last Status Change Date', sortable: true, filterRenderer: MultiSelectFilter, filterable: true },
        { key: 'lastModifiedByUser', name: 'Last Modified By User', sortable: true, filterRenderer: MultiSelectFilter, filterable: true },
        { key: 'lastModifiedByAdmin', name: 'Last Modified By Admin', sortable: true, filterRenderer: MultiSelectFilter, filterable: true }

    ].map(c => ({ ...c, ...columnProps }));

    columns.push({ key: 'editButton', name: 'Edit', formatter: ButtonFormatter, width: 80 })

    exclusions.forEach(exc => {
        let row = {}
        let editFormatted = getEditFormatting(exc, exclusionTypes);

        row.accountName = exc.accountName ? exc.accountName : "";
        row.accountId = exc.accountId ? exc.accountId : "";
        row.requirementId = exc.requirementId ? exc.requirementId : "";
        row.resourceId = exc.resourceId ? exc.resourceId : "";
        row.status = exc.status ? exc.status : "";
        row.type = exc.type ? exc.type : "";
        row.reason = "";
        if (exc.formFields && exc.formFields.reason) {
            row.reason = exc.formFields.reason;
        };

        row.hidesResources = exc.hidesResources ? exc.hidesResources.toString() : "false";
        row.expiration = exc.expirationDate ? exc.expirationDate : "";
        row.adminComments = exc.adminComments ? exc.adminComments : "";
        row.lastStatusChangeDate = exc.lastStatusChangeDate ? exc.lastStatusChangeDate : "";
        row.lastModifiedByUser = exc.lastModifiedByUser ? exc.lastModifiedByUser : "";
        row.lastModifiedByAdmin = exc.lastModifiedByAdmin ? exc.lastModifiedByAdmin : "";
        row.editButton = editFormatted;

        rows.push(row);

    });

    let formatted = {columns: columns, rows: rows};
    return formatted;
}

function getEditFormatting(exc, exclusionTypes) {
    let fields = exc.formFields;
    const formatted = {};
    formatted.fields =[];

    const accountId = {
        label: "Account Id",
        placeholder: "Account Id",
        default: exc.accountId
    };

    const resourceId = {
        label: "Resource Id",
        placeholder: "Resource Id",
        default: exc.resourceId
    };

    const adminComments = {
        label: "Admin Comments",
        placeholder: "Add comments for user",
        default: exc.adminComments
    };

    const expirationDate = {
        label: "Expiration Date",
        placeholder: "Edit exclusions expiration date",
        default: exc.expirationDate
    };

    formatted.modalActions = [{id: "edit", title: "Edit"}];
    formatted.action = "Edit";

    formatted.fields.push(textFieldMaker(accountId, "accountId"));
    formatted.fields.push(textFieldMaker(resourceId, "resourceId"));

    Object.keys(fields).forEach(key => {
        let field = fields[key];

        let fieldObj = {
            label: key,
            placeholder: null,
            default: field
        };

        formatted.fields.push(textFieldMaker(fieldObj, key));
    });

    formatted.fields.push(textFieldMaker(adminComments, "adminComments"));
    formatted.fields.push(textFieldMaker(expirationDate, "expirationDate"));

    formatted.id = exc.exclusionId;
    formatted.display = "Edit";
    formatted.isHidden = exc.hidesResources ? exc.hidesResources : false;
    formatted.kind = "edit";
    formatted.type = exc.status;
    if (exclusionTypes[exc.type]) {
        formatted.dropdown = getDropdown(exclusionTypes[exc.type]);
    }

    return formatted

}

function getDropdown(type) {
    let fields = [];

    Object.keys(type.states).forEach(key => {
        fields.push({state: key});
    });

    return fields;
}

function textFieldMaker(field, key) {
    return {
        type: "field",
        label: field.label,
        placeholder: field.placeholder,
        id: key,
        default: field.default
    }
}

export {
    exclusionsFormatter
}
