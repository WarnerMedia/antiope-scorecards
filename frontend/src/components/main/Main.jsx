import React from 'react';
import Container from '@material-ui/core/Container';
import { Route, Switch, useHistory } from 'react-router-dom';
import AppBar from '@material-ui/core/AppBar';
import Button from '@material-ui/core/Button';
import Toolbar from '@material-ui/core/Toolbar';
import Welcome from '../accounts/Accounts';
import Matrix from '../matrix/Matrix';
import dataSlice from "../../redux/reducers";
import { useDispatch, useSelector } from "react-redux";
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Snackbar from '@material-ui/core/Snackbar';
import dateFormat from 'dateformat';

import NCR from '../ncr/NCR';
import Denied from '../denied/Denied';

import Exclusions from '../exclusions/Exclusions';
import { makeStyles } from '@material-ui/core/styles';
import Logo from '../../logo.png';

import stylesheet from '../styles'
import { Auth, Cache } from 'aws-amplify';

const styles = makeStyles(stylesheet);

function a11yProps(index) {
    return {
      id: `simple-tab-${index}`,
      'aria-controls': `simple-tabpanel-${index}`,
    };
}

export const Main = () => {
    const classes = styles();
    const history = useHistory();
    const status = Cache.getItem('status');
    const dispatch = useDispatch();
    const data = useSelector(state => state.data.index);

    function ReRoute(route) {
        let data = Auth.currentSession()
                    .then(data => {
                        return data;
                    })
                    .catch(err => {
                        return err;
                    });

        if (status && status.isAuthenticated && data !== "No current user") {
            switch(route.location.pathname) {
                case "/accounts":
                    return (<Route path="/accounts" component={Welcome}/>)
                case "/matrix":
                    return (<Route path="/matrix" component={Matrix}/>)
                case "/ncr":
                    return (<Route path="/ncr" component={NCR}/>)
                case "/exclusions":
                    return (<Route path="/exclusions" component={Exclusions}/>)
                default:
                    history.push("/accounts");
                    return (<Route path="/accounts" component={Welcome}/>)

            }

        } else if (status && !status.isAuthenticated && data !== "No current user") {
            return (<Route to="/denied" component={Denied} />)
        } else {
            history.push("/login");
            return (<Route to="/login" />)
        }

    }

    const handleTabChange = (event, newValue) => {
        dispatch(dataSlice.actions.clearState());
        switch (newValue) {
            case 0:
                history.push("/accounts");
                break;
            case 1:
                history.push("/matrix");
                break;
            case 2:
                history.push("/ncr");
                break;
            case 3:
                history.push("/exclusions");
                break;
            default:
                history.push("/accounts");

        }

    }

    const logOut = () => {
        Auth.signOut()
            .then(confirm => {
                history.push("/login");
                dispatch(dataSlice.actions.logOut());
            })
            .catch(err => {
                console.log(err);
            })
    }

    let lastScan = '1976/01/01'

    if (status && status.scan) {
        lastScan = status.scan.lastScanDate;
    }

        return (
            <div className={classes.root}>
                <AppBar position="fixed">
                    <Toolbar>
                        <img alt="" className={classes.logo} src={Logo}/>
                        <Tabs className={classes.tabs} value={data} onChange={handleTabChange} aria-label="simple tabs example">
                            <Tab className={classes.tab}  label="Accounts" {...a11yProps(0)} />
                            <Tab className={classes.tab} label="Matrix" {...a11yProps(1)} />
                            <Tab className={classes.tab} label="NCRs" {...a11yProps(2)} />

                            {status && status.isAdmin && <Tab className={classes.tab} label="Exclusions" {...a11yProps(3)} />}
                        </Tabs>
                        <div className={classes.spacer}></div>
                        <Button color="secondary" onClick={logOut}>Log Out</Button>
                    </Toolbar>
                </AppBar>

                <Container maxWidth='xl'>
                    <main className={classes.content}>
                        <Switch>
                            <ReRoute/>
                        </Switch>
                    </main>
                </Container>
                <Snackbar
                    anchorOrigin={{vertical: 'bottom', horizontal: 'center'}}
                    open={true}
                    message={`Last Scan: ${dateFormat(new Date(lastScan), "yyyy/mm/dd, h:MM:ss TT")} UTC`}
                    key={'bottomCenter'}
                />
            </div>
        );


}

export default Main;
