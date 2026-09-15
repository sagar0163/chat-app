# Plan for Issue #3

- [ ] Create plan file
- [ ] Add `relationship` imports and definitions to models (if using `joinedload`) or write efficient subqueries. Let's use constant number of queries with `IN` clause to avoid modifying models if it's too much, OR add `relationship` and use `selectinload`.
- [ ] Refactor `get_chats` to fetch chats, members, and last messages efficiently.
- [ ] Test the endpoint to ensure it still works correctly.
- [ ] Remove plan file and commit.
