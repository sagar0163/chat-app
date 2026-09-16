# War Room Plan — Issue #6: Prevent unauthorized adding of users to chats

## Progress so far (prior attempt)
- [x] Add `ChatInvite` model + `chat_invites` table
- [x] Make `create_chat` create pending invites for group-chat members instead of adding them directly
- [x] Add `GET /invites`, `POST /invites/{id}/accept`, `POST /invites/{id}/reject`

## Remaining work
- [x] Harden `create_chat`: dedupe member_ids, skip self-invite, validate member IDs exist (400 on unknown)
- [x] Harden invite accept: guard against duplicate membership and missing chat
- [x] Add unique constraint on `chat_invites` (chat_id, invitee_id)
- [x] Write pytest suite covering invite flow, consent-before-membership, and security cases
- [x] Fix pre-existing env breakage: pin bcrypt==4.0.1 (passlib 1.7.4 incompatible with bcrypt>=4.1/5.x)
- [ ] Document invite endpoints in README API table
- [x] Run tests, fix failures (8/8 pass)
- [ ] Clean up plan file and final commit, push branch