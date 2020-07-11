import React from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardActionArea from '@material-ui/core/CardActionArea';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardHeader from '@material-ui/core/CardHeader';
import Typography from '@material-ui/core/Typography';

import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
const styles = makeStyles(stylesheet);

export const Denied = () => {
    const classes = styles();
    return (
        <div className={classes.denied}>
            <Grid
            container
            direction="row"
            justify="center"
            alignItems="center">
                <Grid item xs={6} sm={3}>
                <Card>
                    <CardHeader title="Access Denied"/>
                    <CardActionArea>
                        <CardContent>
                            <Typography variant="h6">Access has been denied.
                                Please go to the link below to inquire about access</Typography>
                        </CardContent>
                    </CardActionArea>
                    <CardContent/>
                    <CardActions>
                        <Button size="small" fullWidth={true} color="primary">
                        Get Access
                        </Button>
                    </CardActions>
                    </Card>
                </Grid>
            </Grid>
        </div>

    )
}

export default Denied;