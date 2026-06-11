# First-User Validation Test

Use this protocol to watch a GIS user try GitMap for the first time. The goal
is not to prove that the user can memorize GitMap commands. The goal is to find
where installation, Portal credentials, item IDs, diff review, and push safety
are unclear.

## Test Goal

A first-time user can complete the core GitMap loop on a non-production ArcGIS
web map:

```bash
gitmap doctor
gitmap doctor --portal
gitmap clone <TEST_ITEM_ID> --directory gitmap-validation-map
cd gitmap-validation-map
gitmap branch feature/validation-change
gitmap checkout feature/validation-change
gitmap pull
gitmap status
gitmap diff --format visual
gitmap commit -m "Validate GitMap workflow"
gitmap diff main feature/validation-change --format visual
gitmap checkout main
gitmap merge feature/validation-change
gitmap push
```

## Safety Requirements

- Use only a disposable web map that the tester owns or has explicit permission
  to modify.
- Do not use production, customer-facing, emergency-response, billing, or
  compliance maps.
- Do not paste real passwords, tokens, private Portal URLs, or production item
  IDs into notes, screenshots, recordings, GitHub issues, or PRs.
- Stop before `gitmap push` if the tester cannot explain which Portal item will
  be updated.
- If the tester is unsure about credentials, item ownership, or write scope,
  record the blocker and stop the test.

## Preparation

1. Create or identify a disposable ArcGIS Online or Portal web map.
2. Confirm the tester can sign in to the ArcGIS organization in a browser.
3. Confirm the tester can safely modify the disposable web map.
4. Create a clean terminal session with no prior GitMap repository state.
5. Have the tester run `gitmap doctor` after install and `gitmap doctor --portal`
   after credentials are configured.
6. Have the tester open the GitMap README and quickstart, but do not coach the
   command sequence unless they are blocked.
7. Start a timer when the tester begins reading the install instructions.

## Observer Checklist

Record short notes for each step:

| Step | Pass criteria | Notes to collect |
|------|---------------|------------------|
| Install | Python 3.11+ venv reaches `gitmap --help` | Python version, shell, install command, error text |
| Credentials | GitMap connects to Portal | Env var or `.env` path used, unclear field names |
| Portal preflight | `gitmap doctor --portal` succeeds or gives a clear blocker | Auth, URL, permission, or package blocker |
| Item ID | Tester finds the web map item ID | Where they looked, any URL confusion |
| Clone | Local repo is created | Output clarity, directory confusion |
| Branch | Feature branch is active | Whether branch naming made sense |
| Pull | Portal data reaches the index | Whether "pull is read-only" was clear |
| Diff | Tester can describe the change | Format used, confusing fields |
| Commit | Commit records the approved state | Message quality, rationale use |
| Merge | Main receives the feature branch | Any Git mental-model mismatch |
| Push | Tester knowingly updates test Portal item | Whether warning language was enough |

## Friction Categories

Tag each issue with one or more categories:

- `install`: Python, package, PATH, shell, virtual environment.
- `credentials`: Portal URL, username/password variables, `.env`, auth errors.
- `portal-preflight`: `gitmap doctor --portal` cannot verify the target
  Portal before clone, pull, or push.
- `item-id`: finding the web map ID or choosing the right item.
- `working-directory`: knowing where the GitMap repo lives.
- `branching`: understanding current branch and branch names.
- `diff-review`: interpreting visual, JSON, or HTML diff output.
- `push-safety`: knowing whether a command reads from or writes to Portal.
- `docs`: unclear wording, missing examples, wrong command, stale screenshot.
- `bug`: command fails when the tester followed the docs correctly.

## Stop Conditions

Stop the test and preserve notes if:

- The tester would need to use a production map to continue.
- Credentials or tokens would need to be shared with the observer.
- `gitmap doctor --portal` reports a credential, URL, permission, or package
  blocker that the tester cannot resolve without observer access to secrets.
- `gitmap push` would update an unknown or unintended item.
- The tester hits an unhandled exception or repeated authentication failure.
- The observer has already coached the same step twice.

## Result Summary Template

```markdown
## GitMap First-User Validation Result

- Tester role:
- Date:
- Environment:
- ArcGIS target: disposable test web map
- Completed core loop: yes/no
- Time to `gitmap --help`:
- Time to `gitmap doctor`:
- `gitmap doctor` result:
- `gitmap doctor --portal` result:
- Time to clone:
- Time to first diff:
- Pushed to test item knowingly: yes/no/not attempted

### Top blockers
- [category] short description

### Confusing but recoverable
- [category] short description

### Follow-up issues to create
- [ ] title
```
