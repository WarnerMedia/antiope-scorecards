import { createSlice } from '@reduxjs/toolkit'
import { getAccountsSummary, getExclusions, getStatus, getNCRs, getAccountsScore, getNCRTags, getScans } from "./middleware";
import { Cache } from 'aws-amplify';


const dataSlice = createSlice({
    name: 'data',
    initialState: {
                data: [],
                modalOpen: {isOpen: false, formData: {}},
                exclusionModalOpen: false,
                isAuthenticated: {auth: false},
                matrixFormatted: {},
                ncrFormatted: {},
                exclusionsFormatted: {},
                accountsFormatted: {},
                scansFormatted: {},
                tags: [],
                currentScan: {},
                index: 0},
    reducers: {
        open: (state, action) => { state.modalOpen = {isOpen: true, formData: action.payload} },
        closed: (state) => { state.modalOpen = {isOpen: false, formData: {}} },
        exclusionOpen: (state) => { state.exclusionModalOpen = true },
        exclusionClosed: (state) => { state.exclusionModalOpen = false },
        setIndex: (state, action) => {
            state.index = action.payload;
        },
        setMatrix: (state, action) => { state.matrixFormatted = action.payload},
        setNCR: (state, action) => { state.ncrFormatted = action.payload},
        setScans: (state, action) => { state.scansFormatted = action.payload},
        setExclusions: (state, action) => { state.exclusionsFormatted = action.payload},
        setAccounts: (state, action) => { state.accountsFormatted = action.payload},
        clearState: (state) => {
            state.matrixFormatted = {};
            state.ncrFormatted = {};
            state.exclusionsFormatted = {};
            state.accountsFormatted = {};
            state.summary = null;
            state.exclusions = null;
            state.ncrRecords = null;
            state.scansRecords = null;
            state.accounts = null;
        },
        logOut: (state) => {
            state.isAuthenticated = {auth: false};
            Cache.clear();
        }
    },
    extraReducers: {
        [getAccountsSummary.fulfilled]: (state, action) => {
            if (action.payload && action.payload.accounts) {
                state.summary = action.payload.accounts;
            }
        },
        [getExclusions.fulfilled]: (state, action) => {
            if (action.payload && action.payload.exclusions) {
                state.exclusions = action.payload.exclusions;
            }
        },
        [getStatus.fulfilled]: (state, action) => {
            Cache.setItem("status", action.payload);
            state.isAuthenticated = {auth: true};
        },
        [getNCRs.fulfilled]: (state, action) => {
            if (action.payload && action.payload.ncrRecords) {
                state.ncrRecords = action.payload.ncrRecords;
            }
        },
        [getScans.fulfilled]: (state, action) => {
            if (action.payload && action.payload.scans) {
                state.scansRecords = action.payload.scans;
            }
        },
        [getNCRTags.fulfilled]: (state, action) => {
            if (action.payload && action.payload.ncrTags) {
                state.tags.push(action.payload.ncrTags);
            }
        },
        [getAccountsScore.fulfilled]: (state, action) => {
            if (action.payload && action.payload.accounts) {
                state.accounts = action.payload.accounts;
            }
        }
    }
});


export default dataSlice;
