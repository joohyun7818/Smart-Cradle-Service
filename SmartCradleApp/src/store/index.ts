import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import agentReducer from './agentSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    agent: agentReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
