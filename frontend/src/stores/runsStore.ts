import { create } from "zustand";
import { fetchRuns, fetchRun } from "../api/runs";
import type { RunSummary, RunDetail } from "../types/run";

export interface RunsState {
  list: RunSummary[];
  listLoading: boolean;
  listError: string | null;
  detail: RunDetail | null;
  detailLoading: boolean;
  detailError: string | null;
  loadList: () => Promise<void>;
  loadDetail: (id: number) => Promise<void>;
}

export const useRunsStore = create<RunsState>((set) => ({
  list: [],
  listLoading: false,
  listError: null,
  detail: null,
  detailLoading: false,
  detailError: null,

  loadList: async () => {
    set({ listLoading: true, listError: null });
    try {
      const list = await fetchRuns();
      set({ list, listLoading: false });
    } catch (e) {
      set({ listLoading: false, listError: e instanceof Error ? e.message : String(e) });
    }
  },

  loadDetail: async (id) => {
    set({ detailLoading: true, detailError: null });
    try {
      const detail = await fetchRun(id);
      set({ detail, detailLoading: false });
    } catch (e) {
      set({ detailLoading: false, detailError: e instanceof Error ? e.message : String(e) });
    }
  },
}));
