# Issue #2: Push Notifications (FCM/APNs) - Continuation Plan

## Already Done (prior commits)
- [x] DeviceToken table model
- [x] Device token registration endpoint (`POST /users/device-token`)
- [x] Mock trigger_push_notifications function
- [x] Broadcast returns offline_users list
- [x] WebSocket handler triggers push for offline users

## Remaining Work
- [ ] Restore requirements-dev.txt for pytest
- [ ] Implement real FCM HTTP v1 API calls using httpx (with service account auth via google-auth)
- [ ] Implement real APNs HTTP/2 calls using httpx (with JWT token generation from EC key)
- [ ] Add device token deletion endpoint (`DELETE /users/device-token`)
- [ ] Update README with new push notification endpoints
- [ ] Add tests for device token registration endpoint
- [ ] Add tests for push notification dispatch logic (mock httpx calls)
- [ ] Add conftest.py with test fixtures
- [ ] Run tests and fix failures
