// Mock storage for testing zustand persist middleware
const createMockStorage = () => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => {
      return store[key] || null;
    },
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    }
  };
};

// Mock localStorage for tests
Object.defineProperty(global, 'localStorage', {
  value: createMockStorage(),
  writable: true
});

// Also define it on window if it exists
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'localStorage', {
    value: createMockStorage(),
    writable: true
  });
}

export default createMockStorage;