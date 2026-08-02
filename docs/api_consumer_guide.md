# API Consumer Guide

This guide is designed for frontend developers integrating client applications with the backend REST APIs.

---

## 1. Authentication & Session APIs

### POST `/auth/login`
*   **Purpose**: Authenticates credentials and sets session cookies.
*   **Request Payload**:
    ```json
    {
      "email": "student@tenant.com",
      "password": "SecurePassword123!",
      "tenant_id": 1
    }
    ```
*   **Response Payload**:
    ```json
    {
      "authenticated": true,
      "access_token": "eyJhbGciOi...",
      "access_token_expires_in": 1800,
      "user": { "email": "student@tenant.com", "role": "student" }
    }
    ```
*   **Error Handling**:
    *   `401 Unauthorized`: Invalid credentials. Show a generic error message.
    *   `429 Too Many Requests`: Rate limit reached. Show a retry countdown.
*   **Best Practices**: Store access tokens in memory and use HTTP secure cookies for refresh tokens.

---

## 2. Diagnostic Assessment APIs

### POST `/diagnostic/submit`
*   **Purpose**: Submits a timed question response and checks test progress.
*   **Request Payload**:
    ```json
    {
      "test_id": "test-session-uuid",
      "question_id": 101,
      "selected_option": 3,
      "time_taken": 15
    }
    ```
*   **Response Payload**:
    ```json
    {
      "test_id": "test-session-uuid",
      "score_updated": true,
      "completed": false
    }
    ```
*   **Error Handling**:
    *   `409 Conflict`: Submission was rejected because the countdown timer expired.
*   **Best Practices**: Debounce submit clicks to prevent duplicate API requests.

---

## 3. Learning Roadmap APIs

### PUT `/roadmap/steps/{step_id}/complete`
*   **Purpose**: Marks a step complete and unlocks subsequent topics.
*   **Request Params**: `step_id` (string path variable).
*   **Response Payload**:
    ```json
    {
      "roadmap_id": "roadmap-uuid",
      "steps": [
        { "id": "step-uuid-99", "status": "completed" }
      ]
    }
    ```
*   **Error Handling**:
    *   `403 Forbidden`: Step does not belong to the user's active tenant scope.
*   **Best Practices**: Invalidate the cached roadmap query in React Query on success to trigger a UI update.

---

## 4. Client Integration Best Practices

*   **Implement Retry Backoffs**: Use exponential backoff retries for network failures (`5xx` errors), but avoid retrying validation failures (`400` or `422` errors).
*   **Verify Active Tokens**: Refresh access tokens before they expire using client interceptors to prevent request failures during active sessions.
