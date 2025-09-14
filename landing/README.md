# Landing Page

This directory contains a static landing page for Ultimate Fantasy.

## How to Run

To view the landing page, you need to run a simple HTTP server from the project's root directory.

1.  **Start the server:**

    ```sh
    python -m http.server 8080 --directory landing
    ```

2.  **Open your browser:**

    Navigate to `http://localhost:8080`.

## Waitlist Functionality

The email signup form on the landing page sends requests to the backend API (`/waitlist`). For the form to work correctly, ensure the backend server is running.
