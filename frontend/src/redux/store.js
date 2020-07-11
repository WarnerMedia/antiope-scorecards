import dataSlice from "./reducers";
import { combineReducers } from "redux";
import { configureStore } from "@reduxjs/toolkit";

const rootReducer = combineReducers({data: dataSlice.reducer});

export default configureStore({reducer: rootReducer});