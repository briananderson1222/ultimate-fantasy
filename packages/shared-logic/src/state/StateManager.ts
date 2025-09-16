import { z } from "zod";

export interface StateManagerConfig {
  persist?: boolean;
  storageKey?: string;
  initialState?: any;
}

export interface StateStore<T = any> {
  getState(): T;
  setState(partial: Partial<T> | ((state: T) => Partial<T>)): void;
  subscribe(listener: (state: T) => void): () => void;
}

export class StateManager {
  private static stores = new Map<string, StateStore>();

  static createStore<T>(
    key: string,
    initialState: T,
    config: StateManagerConfig = {}
  ): StateStore<T> {
    if (this.stores.has(key)) {
      return this.stores.get(key) as StateStore<T>;
    }

    const store = new SimpleStore(initialState, config);
    this.stores.set(key, store);
    return store;
  }

  static getStore<T>(key: string): StateStore<T> | undefined {
    return this.stores.get(key) as StateStore<T>;
  }

  static destroyStore(key: string): void {
    this.stores.delete(key);
  }
}

class SimpleStore<T> implements StateStore<T> {
  private state: T;
  private listeners: Set<(state: T) => void> = new Set();
  private config: StateManagerConfig;

  constructor(initialState: T, config: StateManagerConfig = {}) {
    this.config = config;
    this.state = this.loadPersistedState() || initialState;
  }

  getState(): T {
    return this.state;
  }

  setState(partial: Partial<T> | ((state: T) => Partial<T>)): void {
    const updates = typeof partial === "function" ? partial(this.state) : partial;

    this.state = { ...this.state, ...updates };

    if (this.config.persist) {
      this.persistState();
    }

    this.listeners.forEach(listener => listener(this.state));
  }

  subscribe(listener: (state: T) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private loadPersistedState(): T | null {
    if (!this.config.persist || !this.config.storageKey) {
      return null;
    }

    try {
      if (typeof localStorage !== "undefined") {
        const stored = localStorage.getItem(this.config.storageKey);
        return stored ? JSON.parse(stored) : null;
      }
    } catch (error) {
      console.warn("Failed to load persisted state:", error);
    }

    return null;
  }

  private persistState(): void {
    if (!this.config.storageKey) {
      return;
    }

    try {
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(this.config.storageKey, JSON.stringify(this.state));
      }
    } catch (error) {
      console.warn("Failed to persist state:", error);
    }
  }
}