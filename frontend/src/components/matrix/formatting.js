
import { Filters } from "react-data-grid-addons";
import React from 'react';
import { useHistory } from 'react-router-dom';
import { Row, Cell } from "react-data-grid";
import { makeStyles } from '@material-ui/core/styles';

const { MultiSelectFilter } = Filters;

const useStyles = makeStyles({
    cell: props => ({
        backgroundColor: props.backgroundColor,
        color: props.text
    })
})

function CustomRenderer(props) {
    const history = useHistory();
    return (
        <div
        onClick={() => history.push(`/ncr?accountId=${props.item.column.key}`)}>{props.item.column.name}</div>
    )
}


function CellRenderer(props) {
    let score = {};

    if (props.value !== undefined) {
        score = JSON.parse(props.value);
    }

    if (!score.value) {
        score.value = {numFailing: "0"}
    }

    if (!score.colors) {
        score.colors = {};
        score.colors.background = '#000';
        score.colors.text = '#fff';
    }

    const colors = {backgroundColor: `#${score.colors.background} !important`, text: `#${score.colors.text} !important`};
    const classes = useStyles(colors);
    if (!props.item) {
        let _props = {...props}
        if (score.key === "no") {
            _props.value = score.value;
            return (
                <Cell column={props.column} {..._props} />
            )
        } else {
            _props.value = score.value.numFailing;
            return (
                <Cell className={classes.cell} column={props.column} {..._props} />
            )
        }

    } else {
        return <div></div>
    }

}

const RowRenderer = function(props) {
    let _props = {...props};
    return <Row cellRenderer={CellRenderer} {..._props} />
}

const CustomHeader = item => (<CustomRenderer item={item}>item.column.name</CustomRenderer>);

const columnProps = {
    filterable: true,
    filterRenderer: MultiSelectFilter,
    resizable: true,
};

const matrixFormatter = function(status, scores) {
    let rows = [];
    let filter = {};
    let columns = [
        { key: 'requirement', name: 'Requirement', sortable: true, width: 400},
        { key: 'severity', name: 'Severity', sortable: true, width: 200 },
        { key: 'aggScore', name: 'Agg. Score', width: 200 },
    ];

    columns = columns.map(c => ({ ...c, ...columnProps }));

    scores.forEach(account => {
        if (account.requirementsScores && account.requirementsScores.length > 0) {
            columns.push({key: account.accountId, resizable: true, name: account.accountName, headerRenderer: CustomHeader});
        }
    });

    filter.payers = status.payerAccounts;
    let accounts = [];

    Object.keys(status.requirements).forEach(key => {
        let req = status.requirements[key];
        let row = {};
        let aggScoresArr = [];

        row.severity = JSON.stringify({value: req.severity, key: "no"});
        row.requirement = JSON.stringify({value: `${req.description}`, key: "no"});
        row.requirementId = JSON.stringify({value: req.requirementId, key: "no"});

        scores.forEach(account => {
            if (accounts.indexOf(account.accountId) === -1) {
                accounts.push(account.accountId);
            }

            account.requirementsScores.forEach(item => {
                if (item.requirementId === req.requirementId) {
                    Object.keys(item.score).forEach(key => {
                        let score = item.score[key];
                        let colors = status.severityColors[key];
                        if (score.numFailing === 0 || score.numFailing === "DNC" || score.numFailing === "N/A") {
                            colors = status.severityColors["ok"];
                        }
                        row[account.accountId] = JSON.stringify({value: score, key: key, colors: colors});
                        if (score.numFailing === "DNC" || score.numFailing === "N/A") {
                            aggScoresArr.push(0);
                        } else {
                            aggScoresArr.push(score.numFailing);
                        }

                    })

                }
            });
        });

        if (aggScoresArr.length) {
            let reducedAggScore = aggScoresArr.reduce(function(a, b){
                return a + b;
            }, 0);

            row.aggScore = JSON.stringify({key: "no", value: reducedAggScore.toString()});

            rows.push(row);
        }


    });

    filter.accounts = accounts;

    let formatted = {columns: columns, rows: rows, filter: filter};
    return formatted;
}

export {
    matrixFormatter,
    RowRenderer
}
