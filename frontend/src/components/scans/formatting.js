import React from 'react';
import { Filters } from "react-data-grid-addons";
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
import {EditButton} from "../../utils/Buttons";
import {useHistory} from "react-router-dom";



const styles = makeStyles(stylesheet);
const { MultiSelectFilter } = Filters;

const columnProps = {
    resizable: true
}

const DrillFormatter = ({value, row}) => {
    const history = useHistory();
    const setErrorView = () => {
        history.push('/scans/' + encodeURIComponent(`${value.scanId}`));
    }
    const classes = styles();
    return <EditButton className={classes.tableButtonLargeFont} onClick={() => {setErrorView()}} variant='contained'>View</EditButton>
}

const formatDate = (date) => {
    // yyyy-mm-dd hh:mm:ss
    const pad = (strToPad) => {
        if (strToPad.length === 1) {
            return "0" + strToPad;
        }
        return strToPad;
    }
    let year = String(date.getFullYear());
    let month = pad(String(date.getMonth()));
    let day = pad(String(date.getDate()));

    let hours = pad(String(date.getHours()));
    let minutes = pad(String(date.getMinutes()));
    let seconds = pad(String(date.getSeconds()));

    return year + '-' + month + '-' + day + ' ' + hours + ':' + minutes + ':' + seconds;
}


const scansFormatter = function(scans) {
    let rows = [];
    let columns = [
        { key: 'scanStart', name: 'Scan Start', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 180 },
        { key: 'processState', name: 'Process State', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 120 },
        { key: 'ttl', name: 'Time To Live (TTL)', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 180 },
        { key: 'errors', name: 'Number of Errors', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 180 },
        { key: 'fatalError', name: 'Fatal Error', filterRenderer: MultiSelectFilter, filterable: true, sortable: true, width: 100 },
        { key: 'drill', name: 'View', formatter: DrillFormatter, resizable: true, width: 90 }
    ].map(c => ({ ...c, ...columnProps }));


    scans.forEach(scan => {
        console.log(JSON.stringify(scan));
        if (scan) {
            let row = {};
            let newDate = new Date();
            if (scan.ttl) newDate.setTime(scan.ttl*1000);
            if (newDate) newDate = formatDate(newDate);

            let startDate = new Date(scan.scanId.split("#")[0]);
            if (startDate) startDate = formatDate(startDate);
            row.scanStart = startDate;
            row.processState = scan.processState ? scan.processState : "";
            row.ttl = scan.ttl ? newDate : "";
            row.errors = scan.errors ? scan.errors.length : 0;
            row.fatalError = scan.fatalError ? "yes" : "no";

            row.drill = scan;

            rows.push(row);
            console.log(JSON.stringify(row));
        }

    });


    let formatted = {columns: columns, rows: rows};
    return formatted;
}


export {
    scansFormatter
}
