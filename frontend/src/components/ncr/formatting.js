import React from 'react';
import dataSlice from "../../redux/reducers";
import { useDispatch } from "react-redux";
import { Filters } from "react-data-grid-addons";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import { getNCRTags } from "../../redux/middleware";
import { EditButton, ReviewButton } from '../../utils/Buttons'

const styles = makeStyles(stylesheet);
const { MultiSelectFilter } = Filters;

const columnProps = {
    resizable: true
}

const TagFormatter = ({value, row}) => {
    const dispatch = useDispatch();
    const classes = styles();

    if (value.hasTags) {
        return <div>{value.string}</div>
    }

    return <EditButton className={classes.tableButton} onClick={() => {dispatch(getNCRTags(value.id))}} variant='contained'>Get Tags</EditButton>
}

const ButtonFormatter = ({value, row}) => {
    const dispatch = useDispatch();
    const {actions} = dataSlice;
    const classes = styles();

    return <ReviewButton className={classes.tableButton} onClick={() => {dispatch(actions.open(value))}} variant='contained'>{value.action}</ReviewButton>
}

const RemediationFormatter = ({value}) => {
    const dispatch = useDispatch();
    const {actions} = dataSlice;
    const classes = styles();

    if (!value) {
        return <div></div>
    }

    return <ReviewButton className={classes.tableButton} onClick={() => {dispatch(actions.open(value))}} variant='contained'>{value.action}</ReviewButton>
}

const ncrFormatter = function(status, ncrs, tags) {
    let rows = [];
    let columns = [
        { key: 'accountName', name: 'Account Name', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 160 },
        { key: 'accountId', name: 'Account Id', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 160 },
        { key: 'requirement', name: 'Requirement', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 480 },
        { key: 'resourceId', name: 'Resource Id', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 240 },
        { key: 'resourceType', name: 'Resource Type', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 80 },
        { key: 'severity', name: 'Severity', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 80 },
        { key: 'region', name: 'Region', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 120 },
        { key: 'reason', name: 'Reason', filterRenderer: MultiSelectFilter, filterable: true, width: 480 },
        { key: 'remediation', name: 'Remediation', formatter: RemediationFormatter, resizable: true, width: 160},
        { key: 'exclusionButton', name: 'Edit', formatter: ButtonFormatter, resizable: true, width: 160},
        { key: 'exclusionState', name: 'Exclusion State', filterRenderer: MultiSelectFilter, filterable: true, width: 160},
        { key: 'exclusionExpiration', name: 'Exclusion Expiration', filterRenderer: MultiSelectFilter, filterable: true, width: 160 },
        { key: 'exclusionReason', name: 'Exclusion Reason', width: 160},
        { key: 'tags', name: 'Tags', formatter: TagFormatter, resizable: true, width: 120 }

    ].map(c => ({ ...c, ...columnProps }));

    let requirements = status.requirements;

    ncrs.forEach(ncr => {

        if (!ncr.resource.exclusion || !ncr.resource.exclusion.hidesResources) {
            let row = {};
            let tagFormatting = getTagFormatting(ncr.ncrId, tags);
            let reqId = ncr.resource.requirementId;

            row.accountName = ncr.resource.accountName ? ncr.resource.accountName : "";
            row.accountId = ncr.resource.accountId ? ncr.resource.accountId : "";
            row.severity = getRequirement(requirements, reqId).severity;
            row.resourceId = ncr.resource.resourceId ? ncr.resource.resourceId : "";
            row.resourceType = ncr.resource.resourceType ? ncr.resource.resourceType : "";
            row.region = ncr.resource.region ? ncr.resource.region : "";
            row.requirement = `${getRequirement(requirements, reqId).description}`;
            row.reason = ncr.resource.reason ? ncr.resource.reason : "";
            row.exclusionExpiration = ncr.resource.exclusion ? ncr.resource.exclusion.expirationDate : "";
            row.exclusionState = ncr.resource.exclusion ? ncr.resource.exclusion.status : "";
            row.exclusionReason = ncr.resource.exclusion ? ncr.resource.exclusion.reason : "";

            if (ncr.allowedActions && ncr.allowedActions.remediate) {
                row.remediation = getRemediationFormatting(ncr, status);
            }

            let formatting = getExclusionFormatting(ncr, status);
            row.exclusionButton = formatting;

            row.tags = tagFormatting;
            rows.push(row);
        }

    });


    let formatted = {columns: columns, rows: rows};
    return formatted;
}

function getRequirement(requirements, reqId) {
    let requirement = {}
    requirements.forEach(req => {
        if (req.requirementId === reqId) {
            requirement = req;
        }
    });

    return requirement;
}

function getTagFormatting(id, tags) {
    let tagObject = {hasTags: false, id: id, string: "no tags"};

    if (tags.length === 0) {
        return tagObject;
    } else {
        tags.forEach(tag => {
            if (tag.ncrId === id) {
                tagObject.hasTags = true;
                tag.tags.forEach(pair => {
                    tagObject.string = `${tagObject.string} ${pair.name}:${pair.value}`
                });
            }
        })
    }

    return tagObject;

}

function getExclusionFormatting(ncr, status) {
    const ncrReqId = ncr.resource.requirementId;
    const state = ncr.resource.exclusion ? ncr.resource.exclusion.status : null;
    let expiration = ncr.resource.exclusion ? ncr.resource.exclusion.expirationDate : "";
    const requirements = status.requirements;
    const formData = status.exclusionTypes;
    const formFields = ncr.resource.exclusion ? ncr.resource.exclusion.formFields : null;
    const formatted = {type: "userExclusion", id: ncr.ncrId};

    requirements.forEach(req => {

        if (ncrReqId === req.requirementId) {

            if (req.exclusionType === 'approval | justification | exception') {
                formatted.button = 'approval';
            } else {
                formatted.button = req.exclusionType;
            }
        }

    });

    let f = formData[formatted.button];

    // if (expiration === "") {
    //     let dateVal = 1000 * 3600 * 24 * f.defaultDurationInDays;
    //     let currentDate = new Date().getTime();
    //     let newDate = currentDate + dateVal;

    //     const dateTimeFormat = new Intl.DateTimeFormat('en', { year: 'numeric', month: '2-digit', day: '2-digit' })
    //     const [{ value: month },,{ value: day },,{ value: year }] = dateTimeFormat.formatToParts(newDate);
    //     expiration = `${year}/${month}/${day}`;
    // }

    if (!state) {
        formatted.action = f.states.initial.actionName;
        formatted.modalActions = [{id: "initial", title: f.states.initial.actionName}];
        formatted.fields = formBuilder(null, f.formFields, expiration);
    } else if (state === "initial") {
        formatted.action = "Update";
        formatted.modalActions = [{id: "initial", title: "Update"}];
        formatted.fields = formBuilder(formFields, f.formFields, expiration);
    } else if (state === "approved") {
        formatted.action = "Request Changes";
        formatted.modalActions = [{id: "approved", title: "Request Changes"}];
        formatted.fields = formBuilder(formFields, f.formFields, expiration);
    } else if (state === "rejected") {
        formatted.action = f.states.initial.actionName;
        formatted.modalActions = [{id: "rejected", title: f.states.initial.actionName}];
        formatted.fields = formBuilder(formFields, f.formFields, expiration);
    } else if (state === "archived") {
        formatted.action = "Update";
        formatted.modalActions = [{id: "archived", title: f.states.initial.actionName}];
        formatted.fields = formBuilder(formFields, f.formFields, expiration);
    }

    formatted.display = f.displayname;
    formatted.isHidden = false;

    return formatted;
}

function getRemediationFormatting(ncr, status) {
    const ncrReqId = ncr.resource.requirementId;
    const requirements = status.requirements;
    const formatted = {type: "remediation", id: ncr.ncrId};
    let remediation;

    requirements.forEach(req => {

        if (ncrReqId === req.requirementId) {
            remediation = req.remediation
        }

    });

    formatted.isHidden = false;

    if (remediation) {
        formatted.action = "Remediate";
        formatted.modalActions = [{id: "remediate", title: "Remediate"}];
        formatted.fields = remediationFormBuilder(remediation.parameters);

        formatted.display = "Remediate";

        return formatted;
    } else {
        return null;
    }

}

function remediationFormBuilder(fields) {
    let elements = [];
    Object.keys(fields).forEach(key => {

        elements.push(textFieldMaker(fields[key], key));

    });

    return elements;
}

function formBuilder(oldFields, mainFields, expiration) {
    let elements = [];
    Object.keys(mainFields).forEach(key => {
        if (oldFields && oldFields[key]) {
            elements.push(labelMaker(oldFields[key], key));
        }

        elements.push(textFieldMaker(mainFields[key], key));

    });

    elements.push(textFieldMaker({label: "Expiration Date", placeholder: "yyyy/mm/dd"}, "expirationDate", expiration));

    return elements;
}

function labelMaker(field, key) {

    return {
        type: "label",
        label: `Old ${key}`,
        value: field
    }
}

function textFieldMaker(field, key, expiration) {
    return {
        type: "field",
        label: field.label,
        placeholder: field.placeholder,
        id: key,
        default: expiration
    }
}

export {
    ncrFormatter
}
