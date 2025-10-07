import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Agent, AgentStatus } from '../types';

interface AgentState {
  selectedAgent: Agent | null;
  agentStatus: AgentStatus | null;
  agents: Agent[];
  loading: boolean;
  error: string | null;
}

const initialState: AgentState = {
  selectedAgent: null,
  agentStatus: null,
  agents: [],
  loading: false,
  error: null,
};

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    setSelectedAgent: (state, action: PayloadAction<Agent>) => {
      state.selectedAgent = action.payload;
    },
    setAgentStatus: (state, action: PayloadAction<AgentStatus>) => {
      state.agentStatus = action.payload;
    },
    setAgents: (state, action: PayloadAction<Agent[]>) => {
      state.agents = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setSelectedAgent,
  setAgentStatus,
  setAgents,
  setLoading,
  setError,
} = agentSlice.actions;

export default agentSlice.reducer;
