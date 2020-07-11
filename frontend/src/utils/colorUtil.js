const getColors = function(num) {
    if (num <= 1 && num >= .9) {
      return "#4caf50";
    } else if (num <= .89 && num >= .8) {
      return "#8bc34a";

    } else if (num <= .79 && num >= .7) {
      return "#cddc39";

    } else if (num <= .69 && num >= .6) {
      return "#ffeb3b";

    } else if (num <= .59 && num >= .5) {
      return "#ffc107";

    } else if (num <= .49 && num >= .4) {
      return "#ff9800";

    } else if (num <= .39 && num >= .3) {
      return "#ff5722";

    } else if (num <= .29 && num >= .2) {
      return "#f57c00";

    } else if (num <= .19 && num >= .1) {
      return "#f57c00";

    } else {
      return "#f44336";

    }
}

export default getColors;