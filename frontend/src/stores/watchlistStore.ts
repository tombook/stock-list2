import { create } from "zustand";
import { fetchWatchlist, addWatchlistItem, patchWatchlistItem, deleteWatchlistItem } from "../api/watchlist";
import type { WatchlistItem, WatchlistCreate, WatchlistUpdate } from "../types/watchlist";

export interface WatchlistState {
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  add: (body: WatchlistCreate) => Promise<void>;
  patch: (id: number, body: WatchlistUpdate) => Promise<void>;
  remove: (id: number) => Promise<void>;
}

export const useWatchlistStore = create<WatchlistState>((set, get) => ({
  items: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null });
    try {
      const items = await fetchWatchlist();
      set({ items, loading: false });
    } catch (e) {
      set({ loading: false, error: e instanceof Error ? e.message : String(e) });
    }
  },

  add: async (body) => {
    try {
      const item = await addWatchlistItem(body);
      set({ items: [item, ...get().items] });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    }
  },

  patch: async (id, body) => {
    try {
      const updated = await patchWatchlistItem(id, body);
      set({ items: get().items.map((it) => (it.id === id ? updated : it)) });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    }
  },

  remove: async (id) => {
    try {
      await deleteWatchlistItem(id);
      set({ items: get().items.filter((it) => it.id !== id) });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    }
  },
}));
