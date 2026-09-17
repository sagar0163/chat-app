# Issue #2: Push Notifications (FCM/APNs) - Continuation Plan

## Already Done (prior commits)
- [x] DeviceToken table model
- [x] Device token registration endpoint (`POST /users/device-token`)
- [x] Mock trigger_push_notifications function
- [x] Broadcast returns offline_users list
- [x] WebSocket handler triggers push for offline users

## Remaining Work
- [x] Restore requirements-dev.txt for pytest
- [x] Implement real FCM HTTP v1 API calls using httpx (with service account auth via google-auth/jose RS256)
- [x] Implement real APNs HTTP/2 calls using httpx (with JWT token generation from EC key)
- [x] Add device token deletion endpoint (`DELETE /users/device-token`)
- [x] Update README with new push notification endpoints
- [x] Add conftest.py with test fixtures
- [x] Add tests for device token registration endpoint
- [x] Add tests for push notification dispatch logic (mock httpx calls)
- [x] Run tests and fix failures
