import React from 'react';
import './App.css';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { withStyles } from '@material-ui/core/styles';
import { ThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import Main from '../src/components/main/Main';
import Login from '../src/components/login/Login';


const useStyles = {};

const theme = createMuiTheme({
	palette: {
		primary: {
			main: "#1e1e1e",
		},
		secondary: {
			main: '#e5bc73',
		}
	  },
  });

export const App = () => {

	return (
		<ThemeProvider theme={theme}>
			<div className="App">
				<Router>
					<Switch>
						<Route exact path="/login" component={Login}/>
						<Route path="/">
							<Main/>
						</Route>
					</Switch>
				</Router>
			</div>
		</ThemeProvider>

	);

};


export default withStyles(useStyles)(App);
