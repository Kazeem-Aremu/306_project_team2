# Coding Standards - CSDP306 Team 2

Everyone follows these rules. Reviewers check them on every pull request.

## 1. Language and style
- Python 3.10 or newer, standard library only (plus pytest for running tests, optional).
- Follow PEP 8: 4-space indents, lines of 100 characters or less.
- Names: `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Use clear names over short ones: `technician_id`, not `tid`.

## 2. Where code goes (matches the architecture)
| Layer | File(s) | May contain | Must not contain |
|---|---|---|---|
| Interface | `helpdesk/web.py`, `helpdesk/static/` | Routes that call one service method each; the page's HTML, CSS and JavaScript | Business rules, file access |
| Services | `helpdesk/request_service.py`, `report_service.py` | Validation, permission checks, status changes, counts | `print()`, `input()`, file access |
| Rules | `helpdesk/status_rules.py`, `permissions.py` | The transition table and role/ownership checks | Anything else |
| Storage | `helpdesk/repositories.py` | Reading and writing JSON | Decisions about what is allowed |
| Domain | `helpdesk/models.py` | Data classes and fixed values | File access, UI |

- Status rules live **only** in `status_rules.TRANSITIONS`. Never hard-code a status check anywhere else.
- Every service method that changes data calls `permissions.require(...)` **first**. Hiding a button
  in the page is never the only protection.
- In `app.js`, build elements with `textContent`, never `innerHTML`, so typed text can't inject markup.

## 3. Functions
- One job per function; aim for under 30 lines.
- Every public function has a docstring naming the requirement it serves, e.g. `"""FR-04: assign ..."""`.
- Service methods follow the same order: check permission, validate, change, save.

## 4. Errors
- Raise `ValidationError`, `PermissionDenied` or `TransitionError` with a plain-language message that says what is wrong and how to fix it.
- Services never print. `web.py` turns each error into a message the page shows.
- On any error, nothing is saved.

## 5. Tests
- Every new function gets tests in `tests/` in the same pull request.
- Test names describe the behavior: `test_requester_cannot_assign`.
- Tests extend `DataTestCase` so they work on a copy of the sample data; never edit `data/` from a test.
- Test both the normal case and at least one failure case.
- All tests must pass before merging: `python -m unittest discover -s tests -t .`

## 6. Data
- Simulated data only. No real names, student IDs or campus records anywhere in the repo.

## 7. Git workflow
- Never commit straight to `main`.
- One branch per backlog item: `feature/fr-01-submit`, `fix/summary-counts`.
- Small commits with clear messages in the present tense: `Add title length check (FR-01)`.
- Open a pull request using the template; link the requirement or story.
- Every pull request is reviewed by one team member who did not write it. Reviewers rotate each week.
- The reviewer leaves at least one real comment; the author responds or fixes before merging.
- Merge only when tests pass and the reviewer approves.

## 8. Sources and AI tools
- Note in the pull request description if code came from an outside source or an AI tool, as the course syllabus requires.
- Only merge code you can explain.
