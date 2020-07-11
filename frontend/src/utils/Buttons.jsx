import Button from '@material-ui/core/Button';
import { withStyles } from '@material-ui/core/styles';
import { indigo, purple } from '@material-ui/core/colors';

const EditButton = withStyles((theme) => ({
    root: {
      color: theme.palette.getContrastText(purple[400]),
      backgroundColor: purple[400],
      '&:hover': {
        backgroundColor: purple[600],
      },
    },
}))(Button);

const ReviewButton = withStyles((theme) => ({
    root: {
        color: theme.palette.getContrastText(indigo[400]),
        backgroundColor: indigo[400],
        '&:hover': {
        backgroundColor: indigo[600],
        },
    },
}))(Button);

export {
    ReviewButton,
    EditButton
}
