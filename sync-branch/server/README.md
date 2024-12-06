
# SyncBranch API Documentation

## Overview
This API manages user profiles, messaging, friendships, and authentication. It utilizes JWT for secure authentication and provides endpoints to interact with user data. The API is optimized for Flutter integration and includes Swagger-based documentation for easier usage.

---

## Base URL
The base URL for all endpoints is: `http://<your-server-address>`

---

## Authentication
All endpoints except `/auth/register` and `/auth/login` require a valid JWT token in the `Authorization` header as `Bearer <token>`.

---

## Endpoints

### 1. **Authentication**
#### Register
- **POST** `/auth/register`
- **Description**: Registers a new user.
- **Request Body**:
    ```json
    {
        "username": "example_user",
        "email": "example@example.com",
        "password": "secure_password"
    }
    ```
- **Response**:
    ```json
    {
        "message": "User registered successfully"
    }
    ```

#### Login
- **POST** `/auth/login`
- **Description**: Logs in and returns an access token.
- **Request Body**:
    ```json
    {
        "username": "example_user",
        "password": "secure_password"
    }
    ```
- **Response**:
    ```json
    {
        "access_token": "<jwt_token>"
    }
    ```

---

### 2. **Profile**
#### View Profile
- **GET** `/profile/view`
- **Description**: Retrieves the profile of the authenticated user.
- **Headers**:
    ```http
    Authorization: Bearer <jwt_token>
    ```
- **Response**:
    ```json
    {
        "username": "example_user",
        "email": "example@example.com",
        "spotify_user_id": "spotify123"
    }
    ```

#### Update Profile
- **PUT** `/profile/update`
- **Description**: Updates the profile of the authenticated user.
- **Request Body**:
    ```json
    {
        "email": "new_email@example.com",
        "spotify_user_id": "new_spotify_id"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Profile updated successfully"
    }
    ```

---

### 3. **Messaging**
#### Send Message
- **POST** `/messaging/send`
- **Description**: Sends a message to another user.
- **Request Body**:
    ```json
    {
        "recipient": "recipient_user",
        "message": "Hello!"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Message sent successfully"
    }
    ```

#### Retrieve Messages
- **GET** `/messaging/retrieve`
- **Description**: Retrieves messages for the authenticated user.
- **Query Parameters**:
    - `page`: Page number (default: 1)
    - `per_page`: Messages per page (default: 10)
- **Response**:
    ```json
    {
        "messages": [
            {
                "content": "Hello!",
                "sender": "example_user",
                "sent_at": "2024-01-01T12:00:00"
            }
        ]
    }
    ```

#### Mark Message
- **POST** `/messaging/mark`
- **Description**: Marks a message as read or unread.
- **Request Body**:
    ```json
    {
        "message_id": 123,
        "status": "read"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Message marked as read"
    }
    ```

---

### 4. **Friendship**
#### Send Friend Request
- **POST** `/friendship/send`
- **Description**: Sends a friendship request to another user.
- **Request Body**:
    ```json
    {
        "receiver_username": "recipient_user"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Friendship request sent"
    }
    ```

#### Respond to Friend Request
- **POST** `/friendship/respond`
- **Description**: Responds to a friendship request.
- **Request Body**:
    ```json
    {
        "sender_username": "example_user",
        "response": "accept"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Friendship request accepted"
    }
    ```

#### List Friend Requests
- **GET** `/friendship/list`
- **Description**: Lists friendship requests for the authenticated user.
- **Response**:
    ```json
    {
        "requests": [
            {
                "sender_username": "example_user",
                "status": "pending"
            }
        ]
    }
    ```

---

### 5. **API**
#### Fetch All Records from a Table
- **GET** `/api/table/<table_name>`
- **Description**: Fetches all records from a specified table.
- **Headers**:
    ```http
    Authorization: Bearer <jwt_token>
    ```
- **Response**:
    ```json
    [
        {
            "column1": "value1",
            "column2": "value2"
        }
    ]
    ```

#### Execute a Custom Query
- **POST** `/api/query`
- **Description**: Executes a custom SQL query.
**Possible DB Names**: "flutter", "primary"
- **Request Body**:
    ```json
    {
        "query": "SELECT * FROM users WHERE username = ?",
        "db_name": "flutter"
    }
    ```
- **Response**:
    ```json
    {
        "column1": "value1",
        "column2": "value2"
    }
    ```

---

### 6. **Swagger Documentation**
Access the auto-generated API documentation at:
- URL: `/api/docs`

---

## Notes for Flutter Developers
- Use libraries like `http` or `dio` for making HTTP requests.
- Save the JWT token securely (e.g., `flutter_secure_storage`).
- For pagination, use the `page` and `per_page` query parameters to control the number of items fetched.

---

## Error Handling
All responses include a meaningful `error` message if an issue occurs. Example:
```json
{
    "error": "Invalid username or password"
}
```
