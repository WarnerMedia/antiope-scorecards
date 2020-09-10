import React, { useState, useEffect } from 'react';
import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardHeader from '@material-ui/core/CardHeader';
import TextField from '@material-ui/core/TextField';
import CircularProgress from '@material-ui/core/CircularProgress';

import { useDispatch, useSelector } from "react-redux";
import { getStatus } from "../../redux/middleware";
import { useHistory } from 'react-router-dom';

import Amplify, { Auth, Hub } from 'aws-amplify';
import { makeStyles } from '@material-ui/core/styles';
import stylesheet from '../styles';
const styles = makeStyles(stylesheet);

Amplify.configure({
    Auth: {
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolWebClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
      region: 'us-east-1',
      oauth: {
        domain: `${process.env.REACT_APP_COGNITO_DOMAIN}`,
        scope: ['openid', 'email'],
        redirectSignIn: `https://${window.location.hostname}/callback`,
        redirectSignOut: `https://${window.location.hostname}/login`,
        responseType: 'token'
      }
    },
    Cache: {
        itemMaxSize: 1000000,
        defaultTTL: 604800000,
    }
  });

export const Login = () => {
    const classes = styles();
    const dispatch = useDispatch();
    const data = useSelector(state => state.data.isAuthenticated);
    const history = useHistory();

    useEffect(() => {
        if (data.auth) {
            history.push('/accounts');
        }
        Hub.listen('auth', (data) => {
            Auth.currentSession()
            .then(data => {
                if (data) {
                    setLoading(true);
                    dispatch(getStatus());
                }
            })
            .catch(err => {
                console.log(err);
            });
        });
    }, [data.auth, history, dispatch]);

    const [email, setEmail] = useState("");
    const [password, setPass] = useState("");
    const [verification, setVerification] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);
    const [user, setUser] = useState(false);
    const [resetScreen, setResetScreen] = useState(false);

    const [forgotPassEmail, setForgotPassEmail] = useState(false);

    const [newPassword, setNewPassword] = useState("");

    const handleChange = (event) => {
        if (event.target.name === "email") {
            setEmail(event.target.value);
        } else if (event.target.name === "pass") {
            setPass(event.target.value);
        } else if (event.target.name === "newPass") {
            setNewPassword(event.target.value);
        } else if (event.target.name === "verification") {
            setVerification(event.target.value);
        }
    }

    function setNewPass() {
        setLoading(true);
        Auth.completeNewPassword(user, newPassword)
            .then(user => {
                dispatch(getStatus())
            })
            .catch(err => {
                console.log(err);
                setLoading(false);
                setError(true);
            });
    }

    function signIn() {
        setLoading(true);
        Auth.signIn(email, password)
            .then(user => {
                if (user.challengeName === "NEW_PASSWORD_REQUIRED") {
                    setLoading(false);
                    setEmail('');
                    setPass('');
                    setError(false);
                    setUser(user);
                } else {
                    dispatch(getStatus())
                }
            })
            .catch(e => {
                console.log(e);
                setLoading(false);
                setError(true);
            });
    }

    const handleLogin = () => {
        signIn();
    }

    const handleSetPass = () => {
        setNewPass();
    }

    const handleForgotPass = () => {
        setPass('');
        setError(false);
        setUser(false);
        setForgotPassEmail(true);

    }

    const handleBeginReset = () => {
        setLoading(true);
        Auth.forgotPassword(email)
        .then(data => {
            setLoading(false);
            setError(false);
            setForgotPassEmail(false);
            setResetScreen(true);
        })
        .catch(err => {
            setLoading(false);
            console.log(err);
            setError(true);
        });

    }

    const handleFinalReset = () => {
        setLoading(true);
        Auth.forgotPasswordSubmit(email, verification, newPassword)
        .then(data => {
            setLoading(false);
            setError(false);
            setResetScreen(false);
        })
        .catch(err => {
            setLoading(false);
            console.log(err);
            setError(true);
        });

    }

    const handleOktaLogin = () => {
        Auth.federatedSignIn({customProvider: 'Okta'})
        .then(data => {
            console.log(data);
        })
        .catch(err => {
            console.log(err);
        });
    }

    const handleGoBack = () => {
        setForgotPassEmail(false);
        setResetScreen(false);
    }

    if (user) {
        return (
            <div className={classes.root}>
                <Grid
                container
                direction="row"
                justify="center"
                alignItems="center">
                    <Grid item xs={6} sm={3}>
                    <Card>
                           <CardHeader title="Set New Password"/>
                            <CardContent>
                                <TextField
                                    margin="dense"
                                    id="newPass"
                                    name="newPass"
                                    error={error}
                                    type="password"
                                    label="New Password"
                                    value={newPassword || ''}
                                    onChange={handleChange}
                                    fullWidth
                                />
                            </CardContent>
                        <CardContent/>
                        <CardActions>
                            <div className={classes.wrapper}>
                                <Button onClick={handleSetPass} size="small" color="primary">
                                    Login
                                </Button>
                                {loading && <CircularProgress size={20} className={classes.buttonProgress} />}
                            </div>
                        </CardActions>
                        </Card>
                    </Grid>
                </Grid>
            </div>)
    } else if (forgotPassEmail) {
        return (
            <div className={classes.root}>
                <Grid
                container
                direction="row"
                justify="center"
                alignItems="center">
                    <Grid item xs={6} sm={3}>
                    <Card>
                            <CardHeader title="Set New Password"/>
                            <CardContent>
                            <TextField
                                    autoFocus
                                    margin="dense"
                                    id="name"
                                    name="email"
                                    error={error}
                                    label="Email Address"
                                    type="email"
                                    value={email || ''}
                                    onChange={handleChange}
                                    fullWidth
                                />
                            </CardContent>
                        <CardContent/>
                        <CardActions>
                                <Button onClick={handleGoBack} size="small" color="primary">
                                    Cancel
                                </Button>
                            <div className={classes.wrapper}>
                                <Button onClick={handleBeginReset} size="small" color="primary">
                                    Submit
                                </Button>
                                {loading && <CircularProgress size={20} className={classes.buttonProgress} />}
                            </div>
                        </CardActions>
                        </Card>
                    </Grid>
                </Grid>
            </div>)

    } else if (resetScreen) {
        return (
            <div className={classes.root}>
                <Grid
                container
                direction="row"
                justify="center"
                alignItems="center">
                    <Grid item xs={6} sm={3}>
                    <Card>
                           <CardHeader title="Set New Password"/>
                            <CardContent>
                                <TextField
                                        autoFocus
                                        margin="dense"
                                        id="name"
                                        name="verification"
                                        error={error}
                                        label="Verification Code"
                                        type="email"
                                        value={verification || ''}
                                        onChange={handleChange}
                                        fullWidth
                                    />
                                    <TextField
                                        margin="dense"
                                        id="newPass"
                                        name="newPass"
                                        error={error}
                                        type="password"
                                        label="New Password"
                                        value={newPassword || ''}
                                        onChange={handleChange}
                                        fullWidth
                                    />
                            </CardContent>
                        <CardContent/>
                        <CardActions>
                                <Button onClick={handleGoBack} size="small" color="primary">
                                    Cancel
                                </Button>
                            <div className={classes.wrapper}>
                                <Button onClick={handleFinalReset} size="small" color="primary">
                                    Submit
                                </Button>
                                {loading && <CircularProgress size={20} className={classes.buttonProgress} />}
                            </div>
                        </CardActions>
                        </Card>
                    </Grid>
                </Grid>
            </div>)
    } else {
        return (
            <div className={classes.root}>
                <Grid
                container
                direction="row"
                justify="center"
                alignItems="center">
                    <Grid item xs={6} sm={3}>
                    <Card>
                           <CardHeader title="Login"/>
                            <CardContent>
                                <TextField
                                    autoFocus
                                    margin="dense"
                                    id="name"
                                    name="email"
                                    error={error}
                                    label="Email Address"
                                    type="email"
                                    value={email || ''}
                                    onChange={handleChange}
                                    fullWidth
                                />
                                <TextField
                                    margin="dense"
                                    id="name"
                                    name="pass"
                                    error={error}
                                    label="Password"
                                    type="password"
                                    value={password || ''}
                                    onChange={handleChange}
                                    fullWidth
                                />
                            </CardContent>
                        <CardContent/>
                        <CardActions>
                            <div className={classes.wrapper}>
                                <Button onClick={handleOktaLogin} variant="contained" size="small" color="secondary">
                                Okta
                                </Button>
                            </div>
                            <div className={classes.wrapper}>
                                <Button onClick={handleLogin} size="small" color="primary">
                                Login
                                </Button>
                            </div>
                            <div className={classes.wrapper}>
                                <Button onClick={handleForgotPass} size="small" color="primary">
                                Forgot Password
                                </Button>
                            </div>
                        </CardActions>
                        {loading && <CircularProgress size={80} className={classes.loginProgress} />}

                        </Card>
                    </Grid>
                </Grid>
            </div>)
    }



}

export default Login;
