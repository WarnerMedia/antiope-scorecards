import _ from 'lodash';
import { createAsyncThunk } from '@reduxjs/toolkit'
import { Auth } from "aws-amplify";
import axios from 'axios';
import querystring from 'querystring';

const ACCOUNT_CHUNK_SIZE = 50;

const getStatus = createAsyncThunk(
    'data/getStatus',
    async (id, thunkAPI) => {
            try {
                const auth = await Auth.currentSession();
                const config = {
                    headers: {
                        'Authorization': auth.idToken.jwtToken,
                    }
                };

                const d = await axios.get(`${process.env.REACT_APP_API_URL}/status`, config);
                return d.data;

            } catch(error) {
                return error.response.data;

            }

    }
)

const getAccountsSummary = createAsyncThunk(
    'data/getAccountsSummary',
    async (accountIds, thunkAPI) => {
        const accountIdChunks = _.chunk(accountIds, ACCOUNT_CHUNK_SIZE);
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };
            const promisedChunks = accountIdChunks.map(async accountIdChunk => {
                const d = await axios.get(`${process.env.REACT_APP_API_URL}/accounts/${accountIdChunk.join()}/summary`, config);
                return d.data;
            });
            const resolvedChunks = await Promise.all(promisedChunks);
            const result = resolvedChunks.reduce((accumulator, currentValue) => {
                accumulator.accounts = accumulator.accounts.concat(currentValue.accounts);
                return accumulator;
            });
            return result;
        } catch(error) {
            return console.log(error.response.data);

        }

    }
)

const getAccountsScore = createAsyncThunk(
    'data/getAccountsScore',
    async (accountIds, thunkAPI) => {
        const accountIdChunks = _.chunk(accountIds, ACCOUNT_CHUNK_SIZE);
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };
            const promisedChunks = accountIdChunks.map(async accountIdChunk => {
                const d = await axios.get(`${process.env.REACT_APP_API_URL}/accounts/${accountIdChunk}/detailedScore`, config);
                return d.data;
            });
            const resolvedChunks = await Promise.all(promisedChunks);
            const result = resolvedChunks.reduce((accumulator, currentValue) => {
                accumulator.accounts = accumulator.accounts.concat(currentValue.accounts);
                return accumulator;
            });
            return result;


        } catch(error) {
            return console.log(error.response.data);

        }

    }
)

const getNCRs = createAsyncThunk(
    'data/getNCRs',
    async (request) => {
        let { accountId, requirementId } = request;
        if (!Array.isArray(accountId)) {
            accountId = [accountId];
        }

        const accountIdChunks = _.chunk(accountId, ACCOUNT_CHUNK_SIZE);
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };
            const promisedChunks = accountIdChunks.map(async accountIdChunk => {
                const qsparams = {
                    accountId: accountIdChunk,
                };
                if (requirementId) qsparams.requirementId = requirementId;
                const qs = querystring.encode(qsparams);
                const d = await axios.get(`${process.env.REACT_APP_API_URL}/ncr?${qs}`, config);
                return d.data;
            });
            const resolvedChunks = await Promise.all(promisedChunks);
            const result = resolvedChunks.reduce((accumulator, currentValue) => {
                accumulator.ncrRecords = accumulator.ncrRecords.concat(currentValue.ncrRecords);
                return accumulator;
            });
            return result;

        } catch(error) {
            return console.log(error.response.data);

        }

    }
)

const getNCRTags = createAsyncThunk(
    'data/getNCRTags',
    async (ncrId) => {
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };
            ncrId = encodeURIComponent(ncrId);
            const d = await axios.get(`${process.env.REACT_APP_API_URL}/ncr/${ncrId}/tags`, config);
            return d.data;

        } catch(error) {
            return console.log(error.response.data);

        }

    }
)

const getExclusions = createAsyncThunk(
    'data/getExclusions',
    async (id, thunkAPI) => {
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };

            const d = await axios.get(`${process.env.REACT_APP_API_URL}/exclusions`, config);
            return d.data;

        } catch(error) {
            return console.log(error.response.data);

        }
    }
)

const putExclusions = createAsyncThunk(
    'data/putExclusions',
    async (body, thunkAPI) => {
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                },
                body: body
            };

            const d = await axios.put(`${process.env.REACT_APP_API_URL}/exclusions`, body, config);
            return d.data;

        } catch(error) {
            return error;

        }
    }
)

const putExclusionsUser = createAsyncThunk(
    'data/putExclusionsUser',
    async (body, thunkAPI) => {
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };

            const d = await axios.put(`${process.env.REACT_APP_API_URL}/exclusions/user`, body, config);
            return d.data;

        } catch(error) {
            return error;

        }
    }
)

const postRemediation = createAsyncThunk(
    'data/postRemediation',
    async (body, thunkAPI) => {
        try {
            const auth = await Auth.currentSession();
            const config = {
                headers: {
                    'Authorization': auth.idToken.jwtToken,
                }
            };

            const d = await axios.post(`${process.env.REACT_APP_API_URL}/remediate`, body, config);
            return d.data;

        } catch(error) {
            return error;

        }
    }
)

export {
    getStatus,
    getAccountsSummary,
    getAccountsScore,
    getExclusions,
    getNCRs,
    getNCRTags,
    postRemediation,
    putExclusions,
    putExclusionsUser
};
