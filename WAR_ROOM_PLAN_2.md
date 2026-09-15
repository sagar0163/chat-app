# Plan for Issue #2

- [x] Add `DeviceToken` table model (id, user_id, token) and update DB setup.
- [ ] Add POST `/users/device-token` endpoint to register tokens.
- [ ] Add FCM/APNs push notification logic (mock or simple implementation for `trigger_push_notification`).
- [ ] Update `websocket_endpoint` and `send_message` logic to trigger push notifications for offline users in the chat.
