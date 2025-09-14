# 3. Use React Query for Server State Management

- **Status:** Accepted
- **Date:** 2025-09-14

## Context

Our frontend application needs a robust solution for fetching, caching, and synchronizing data from the backend API. This is often referred to as "server state" management. The solution should simplify data fetching logic, handle caching and re-fetching automatically, and integrate well with our Next.js and React codebase.

## Decision

We have decided to use **React Query** (now known as TanStack Query) for managing server state in our frontend application.

## Rationale

React Query was chosen for the following reasons:

1.  **Declarative Data Fetching:** React Query provides a simple, hook-based API for fetching and updating data. It abstracts away the complexities of `useEffect` and `useState` for data fetching, leading to cleaner and more maintainable component code.

2.  **Automatic Caching and Re-fetching:** React Query automatically handles caching, background re-fetching, and stale-while-revalidate logic. This ensures that the data displayed to the user is always fresh, without requiring manual intervention.

3.  **Improved User Experience:** Features like optimistic updates allow for a more responsive and seamless user experience. When a user performs a mutation (e.g., updating their settings), the UI can be updated instantly, before the server has even responded.

4.  **Devtools:** React Query comes with excellent developer tools that make it easy to inspect cached data, understand query states, and debug data fetching issues.

5.  **Separation of Concerns:** It encourages a clear separation between server state (managed by React Query) and client state (e.g., form inputs, modal visibility), which can be managed with `useState` or other client state management libraries if needed.

### Alternatives Considered

-   **Redux / Redux Toolkit:** While powerful for managing global client state, Redux is not specifically designed for server state. Using it for API data often requires a significant amount of boilerplate (actions, reducers, middleware like thunks or sagas).
-   **SWR:** SWR is another excellent library for server state management and is very similar to React Query. We chose React Query due to its slightly larger feature set (e.g., optimistic updates) and our team's prior experience with it.
-   **Apollo Client:** Apollo Client is a great choice for GraphQL APIs, but since our backend exposes a RESTful API, React Query is a more natural fit.
