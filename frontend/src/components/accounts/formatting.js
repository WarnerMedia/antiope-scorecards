import React from 'react';
import { Filters } from "react-data-grid-addons";

const { MultiSelectFilter } = Filters;

const columnProps = {
    resizable: true
}

const CurrentScoreFormatter = ({value}) => {
    return <div className={value.class}>{value.number}</div>
}

const LinkFormatter = ({value}) => {
    return <a target="_blank" rel="noopener noreferrer" href={value}>download</a>
}

const accountsFormatter = function(status, summary) {
    let rows = [];
    let filter = {};
    let dateColumns = [];
    let columns = [
        { key: 'accountId', name: 'Account Id', filterRenderer: MultiSelectFilter, filterable: true, sortable: true },
        { key: 'accountName', name: 'Account Name', filterRenderer: MultiSelectFilter, filterable: true, sortable: true },
        { key: 'currentScore', name: 'Current Score', formatter: CurrentScoreFormatter }
    ];

    summary.forEach(item => {
        item.historicalScores.forEach(score => {
            if (dateColumns.indexOf(score.date) === -1) {
                dateColumns.push(score.date);
            }
        });
    });

    filter.payers = status.payerAccounts;
    let accounts = [];

    dateColumns.sort((a,b) => {
        return new Date(b) - new Date(a);
    });

    dateColumns.forEach(score => {
        columns.push({key: score, name: `Score ${score}` })
    });

    columns = columns.concat([
                            {key: 'criticalCount', name: 'Critical Findings', filterRenderer: MultiSelectFilter, filterable: true},
                            { key: 'docButton', name: 'Spreadsheet', formatter: LinkFormatter, resizable: true, width: 160},

                        ]);

    columns = columns.map(c => ({ ...c, ...columnProps }));

    summary.forEach(item => {
        if (accounts.indexOf(item.accountId) === -1) {
            accounts.push(item.accountId);
        }

        let row = {};
        let currentScore = item.currentScore ? item.currentScore : 0;
        let formatterValue = {class: "black", number: currentScore}
        row.accountId = item.accountId ? item.accountId: "";
        row.accountName = item.accountName ? item.accountName: "";
        dateColumns.forEach(date => {
            row[date] = 0
        });

        item.historicalScores.forEach(hist => {
            row[hist.date] = hist.score ? hist.score : 0;
        });

        if (dateColumns.length > 0) {
            const lastWeek = dateColumns[0];
            const number = currentScore - row[lastWeek];

            if (Math.sign(number) === -1) {
                formatterValue.number = `${currentScore} (↓${number})`;
                formatterValue.class = 'green-color';
            } else if (Math.sign(number) === 1) {
                formatterValue.number = `${currentScore} (↑${number})`;
                formatterValue.class = 'red-color';

            }

        }

        row.currentScore = formatterValue;
        row.criticalCount = item.criticalCount ? item.criticalCount : 0;
        row.docButton = item.spreadsheetDownload ?  item.spreadsheetDownload.url : "";

        rows.push(row);

    });

    filter.accounts = accounts;

    let formatted = {columns: columns, rows: rows, filter: filter};
    return formatted;
}

export {
    accountsFormatter
}
