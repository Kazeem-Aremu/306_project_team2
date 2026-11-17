# Campus Technology Help Desk System

CSDP306 Project A, Team 2. A locally run prototype where requesters submit and track technology
issues, a coordinator reviews, prioritizes and assigns them, and technicians record progress and
resolutions. Uses simulated data only.

**Team:** Andie Kollie, Osa Osifo, Kazeem Aremu, Ky'Reh Buchanan, Padma Waiba

## Requirements
- Python 3.10 or newer (`python --version` to check)
- No other packages are needed to run the app or the tests. pytest is optional.
- A web browser (Safari, Chrome, Edge or Firefox).
- No internet connection, separate server or database. The app runs its own small local web
  server that only this computer can reach.

## Setup
```bash
git clone https://github.com/Kazeem-Aremu/306_project_team2.git
cd 306_project_team2
```
On some systems the command is `python3` instead of `python`.

## Run the app
```bash
python -m helpdesk
```
Your browser opens the help desk page (if it doesn't, go to the address printed in the terminal,
usually http://127.0.0.1:8000). Pick a role, then a sample user. Each role sees only its own
sections. Use **Switch user** to change role. Press **Ctrl+C** in the terminal to stop the app.


## Run the tests
```bash
python -m unittest discover -s tests -t .
# or, if pytest is installed:
python -m pytest
```

## Sample users (simulated)
| ID | Name | Role |
|---|---|---|
| U-101 | Jordan Sample | Requester |
| U-102 | Riley Example | Requester |
| U-103 | Casey Test | Requester |
| C-01 | Morgan Coordinator | Coordinator |
| T-01 | Alex Tech | Technician |
| T-02 | Sam Tech | Technician |
| T-03 | Jamie Tech | Technician |

`data/requests.json` starts with 8 sample requests, one or more in every status.

## What each role can do
| Role | Can do |
|---|---|
| Requester | Submit a request; see own requests, their status history and resolution notes; cancel own request while it is Submitted |
| Coordinator | See all requests; review (category, priority); assign a technician; close, cancel, unassign or reopen; add admin notes; search and filter; view the activity summary |
| Technician | See assigned requests; start, pause (Waiting) and resume work; add work notes; resolve with a resolution note |

Anything a role is not allowed to do is refused by the server with a message explaining why, even if
someone bypasses the page.

## Project structure
```
helpdesk/
  web.py              local web server and JSON API (interface layer)
  static/             the browser page: index.html, style.css, app.js
  request_service.py  business rules for requests
  report_service.py   activity summary counts
  status_rules.py     allowed status changes (one table)
  permissions.py      role and ownership checks
  repositories.py     JSON loading and saving
  models.py           domain classes
data/                 users.json, requests.json, notes.json
tests/                unit and workflow tests
docs/models/          UML diagrams and their source files
meetings/             sprint planning, review and retrospective notes
```

## Data storage
Data is kept in the three JSON files in `data/`. Every change is saved immediately: the file is
written to a temporary copy first and then renamed, so a crash cannot leave a half-written file.
To reset the sample data, restore `data/` from Git: `git checkout -- data/`.

## Known limitations
- Login is simulated with a role picker; there are no passwords.
- One person uses the app at a time.
- Categories and priorities are fixed.
- Resolved requests count as closed in the summary (pending instructor confirmation).
<!-- Update this list at each milestone. -->
