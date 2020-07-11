import _ from 'lodash';

const clean = function(filtering, input) {

    if (filtering.payers && filtering.payers.length > 0) {
        let newInput = [];

        input.forEach(item => {
            filtering.payers.forEach(payer => {
                if (item.accountId === payer.accountId) {
                    newInput.push(item);
                }
            })
        })

        input = newInput;

    }

    if (filtering.other && Object.entries(filtering.other).length > 0) {
        input = _.filter(input, filtering.other);
    }

    if (filtering.search && filtering.search.length > 0) {
        input = input.filter(obj => {
            var y = false;
            _.valuesIn(obj).forEach(val => {
                if (_.includes(val, filtering.search)) {
                    y = true;
                }
            })

            if (y) {
                return obj;
            }
            return null;
        });
    }

    return input;

}

export default clean;
