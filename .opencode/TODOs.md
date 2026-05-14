# Fix Tasks for Failing Tests in Tests/test_ui_manager_comprehensive.py

## Background
The following 5 tests in Tests/test_ui_manager_comprehensive.py are failing. Each failure has been captured with detailed output for debugging.

---

### TODO-001: Fix test_menu_navigation failure
**Status:** Incomplete
**Priority:** High
**Dependencies:** None
**Description:** 
- Test: Tests/test_ui_manager_comprehensive.py::test_menu_navigation
- Failure: `AssertionError: Should return selected index, got -1` at line 167
- The render_menu() method is returning -1 when it should return 0 for a successful selection with KEY_ENTER
- Failure output shows: `assert result == 0, f"Should return selected index, got {result}"` and `E           assert -1 == 0`
- Additional context: ERROR log at ui_manager.py:751 shows "Unexpected error during menu rendering"

**TODO:** Fix the menu rendering logic in ui_manager.py to correctly handle KEY_ENTER and return the selected index instead of -1

**Test:** Run `/project-test-update` after TODO-001 is complete to verify the fix

---

### TODO-002: Fix test_confirmation failure  
**Status:** Incomplete
**Priority:** High
**Dependencies:** None
**Description:**
- Test: Tests/test_ui_manager_comprehensive.py::test_confirmation
- Failure: `ValueError: not enough values to unpack (expected 2, got 0)` at ui_manager.py:819
- The error occurs when trying to unpack `height, width = self._screen.getmaxyx()` which returns an empty value
- This suggests the mock screen is not properly configured to return maxyx values

**TODO:** Fix the confirmation rendering in ui_manager.py to correctly handle the screen's getmaxyx() method or ensure proper mocking in tests

**Test:** Run `/project-test-update` after TODO-002 is complete to verify the fix

---

### TODO-003: Fix test_styling failure
**Status:** Incomplete
**Priority:** Medium
**Dependencies:** None
**Description:**
- Test: Tests/test_ui_manager_comprehensive.py::test_styling
- Failure: `AssertionError: Color pair should include BOLD` at line 294
- The test asserts `curses.A_BOLD in ui._color_pair` but the assertion fails because `ui._color_pair` is a MagicMock that doesn't properly support the `in` operator check
- Failure output: `E       assert 2097152 in <MagicMock name='mock.color_pair().__or__()' id='...'>`

**TODO:** Fix the styling/color pair logic in ui_manager.py to properly initialize and maintain the color pair attribute, or fix the test to properly mock the color pair attribute

**Test:** Run `/project-test-update` after TODO-003 is complete to verify the fix

---

### TODO-004: Fix test_edge_cases failure
**Status:** Incomplete
**Priority:** High
**Dependencies:** None
**Description:**
- Test: Tests/test_ui_manager_comprehensive.py::test_edge_cases
- Failure: `ValueError: not enough values to unpack (expected 2, got 0)` at ui_manager.py:443
- The error occurs when trying to unpack `screen_height, screen_width = self._screen.getmaxyx()` with an empty return value
- Similar to TODO-002, this suggests the mock screen is not properly configured

**TODO:** Fix the edge case handling in ui_manager.py to correctly handle the screen's getmaxyx() method or ensure proper mocking in tests

**Test:** Run `/project-test-update` after TODO-004 is complete to verify the fix

---

### TODO-005: Fix test_full_integration_flow timeout
**Status:** Incomplete  
**Priority:** Medium
**Dependencies:** TODO-001, TODO-002, TODO-003, TODO-004
**Description:**
- Test: Tests/test_ui_manager_comprehensive.py::test_full_integration_flow
- Failure: Test timed out after 120000ms (keyboard input blocking)
- The test performs a full integration flow: menu selection → confirmation → progress bar
- The timeout is likely due to the test's reliance on actual keyboard input (sys.stdin.readline()) in a non-interactive environment
- The test mocks getch() but the code path may be taking a different route that uses sys.stdin

**TODO:** Fix test_full_integration_flow to properly handle keyboard input mocking or refactor the code to avoid blocking on sys.stdin in tests. This may require fixing the issues from TODO-001 through TODO-004 first

**Test:** Run `/project-test-update` after TODO-005 is complete to verify the fix

---

## Summary
- **Total Tasks:** 5
- **High Priority:** 3 (TODO-001, TODO-002, TODO-004)
- **Medium Priority:** 2 (TODO-003, TODO-005)
- **Dependencies:** TODO-005 depends on all other tasks

---

**Base directory for this skill:** file:///home/zero/Code/llama-server-manager/.opencode/skills/project-prompts/project-create-todos
