// Store event system for inter-store communication
type EventListener = (...args: any[]) => void;

class StoreEventEmitter {
  private listeners: Map<string, EventListener[]> = new Map();

  on(event: string, listener: EventListener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }

  off(event: string, listener: EventListener) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(listener);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  emit(event: string, ...args: any[]) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(listener => listener(...args));
    }
  }

  clear() {
    this.listeners.clear();
  }
}

// Global event emitter for store communication
export const storeEvents = new StoreEventEmitter();

// Event types
export const STORE_EVENTS = {
  USER_LOGIN: 'user:login',
  USER_LOGOUT: 'user:logout',
  LEAGUE_SELECTED: 'league:selected',
  LEAGUE_REFRESH_NEEDED: 'league:refresh_needed',
  LINEUP_SAVED: 'lineup:saved',
  DRAFT_PICK_MADE: 'draft:pick:made',
  TRADE_PROPOSED: 'trade:proposed',
  TRADE_ACCEPTED: 'trade:accepted',
  TRADE_REJECTED: 'trade:rejected',
  TRADE_CANCELLED: 'trade:cancelled',
  TRADE_EVALUATED: 'trade:evaluated',
  WAIVER_CLAIMED: 'waiver:claimed'
} as const;