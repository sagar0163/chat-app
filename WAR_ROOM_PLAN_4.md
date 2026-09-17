# War Room Plan — Issue #4: Cache chat members in WebSocket broadcast

Context: Prior attempt (commits d60b850, ae68639, 7305589) implemented the
Redis cache in `backend/main.py`, but the branch was based on an outdated
`main` that predates the invite system (#6) and upload feature (#1). Rebasing
onto current `main` is required so the PR does not delete those features.

## Subtasks

- [ ] Rebase `war-room-issue-4` onto current `main`
- [ ] Re-apply cache changes to `backend/main.py`:
      `get_chat_member_ids()` (Redis-first, DB fallback + populate)
      `invalidate_chat_members_cache()`
      `broadcast()` uses `get_chat_member_ids()`
      invalidate member cache in `leave_chat`
- [ ] Add unit tests for member-ID cache (hit/miss, invalidate on leave)
- [ ] Run `pytest` in backend/ and confirm suite passes
- [ ] Final review of `git diff main..war-room-issue-4` (cache changes only)
- [ ] Delete WAR_ROOM_PLAN_4.md, final commit referencing #4, push branch