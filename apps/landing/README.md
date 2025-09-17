# Ultimate Fantasy — Landing Page

This directory contains a static landing page for the Ultimate Fantasy platform. It is designed to be simple, fast, and visually appealing, with a primary goal of capturing user interest and collecting emails for a waitlist.

## Overview

The landing page consists of a single HTML file, a CSS file for styling, and a JavaScript file for interactivity. It is fully self-contained and has no build process.

-   `index.html`: The main HTML structure of the page.
-   `style.css`: Contains all the styles, including a dark, stadium-themed design and animations.
-   `script.js`: Handles the waitlist form submission, providing client-side validation and communication with the backend API.

## How to Run

To view the landing page, you can serve the `landing` directory using any simple HTTP server. A common method is to use Python's built-in server.

1.  **Navigate to the project root directory.**

2.  **Start the server:**

    ```bash
    python -m http.server 8080 --directory landing
    ```

3.  **Open your browser:**

    Navigate to [http://localhost:8080](http://localhost:8080).

## Waitlist Functionality

The email signup form on the landing page is designed to send a `POST` request to the `/waitlist` endpoint of the backend API.

-   The API endpoint is hardcoded in `script.js` to `http://localhost:8000/waitlist`. For the form to work correctly, ensure the backend server is running and accessible at this address.
-   The script provides user feedback for success and error states (e.g., "You're on the list!" or "This email is already on the waitlist.").
-   Basic email validation is performed on the client-side before submitting.

## Customization

-   **Text and Content**: All text and content can be directly edited in `index.html`.
-   **Styling**: Colors, fonts, and other visual elements can be modified in `style.css`. The theme is based on CSS variables defined at the top of the file.
-   **API Endpoint**: To change the target API for the waitlist form, update the `apiBaseUrl` constant in `script.js`.