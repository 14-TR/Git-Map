# First-User Feedback Questionnaire

Use this after the first-user validation test. Keep answers short and concrete.
The best feedback names the exact instruction, command, warning, or output that
changed the tester's confidence.

## Tester Context

1. What is your GIS role?
2. Which ArcGIS environment did you use?
3. Which operating system and shell did you use?
4. Had you used Git, command-line GIS tools, or Python virtual environments
   before this test?

## Install And Setup

1. How easy was it to install GitMap and reach `gitmap --help`?
2. Which setup step took the longest?
3. Were the Python and package requirements clear?
4. Were Portal credential instructions clear enough to complete without help?
5. What error message, if any, was hardest to understand?

## Item ID And Clone

1. Was it obvious where to find the ArcGIS web map item ID?
2. Did you feel confident that the map was safe to test against?
3. Did the clone output make it clear where the local repository was created?
4. Was the difference between the Portal item and the local GitMap repository
   clear?

## Branch, Pull, And Diff

1. Did branch creation and checkout match your expectations?
2. Before running `gitmap pull`, did you understand that it reads from Portal
   and updates local staged state?
3. Which diff format did you use?
4. Could you explain what changed from the diff output?
5. What information was missing from the diff for a GIS review?

## Commit, Merge, And Push

1. Did `gitmap commit` feel like it saved the right thing?
2. Did the merge step make sense?
3. Before `gitmap push`, could you identify exactly which Portal item would be
   updated?
4. Were the push warnings strong enough?
5. What would make you more comfortable pushing to a non-production map?

## Trust And Adoption

1. What was the first moment GitMap made sense?
2. What was the first moment you stopped trusting the workflow?
3. Would you try this again on another disposable map?
4. What would block you from recommending GitMap to another GIS user?
5. What one thing should GitMap improve before broader public adoption?

## Issue Conversion

For each problem, capture:

```markdown
- Category:
- Command or doc page:
- Expected result:
- Actual result:
- Exact error or confusing text:
- Suggested fix:
```
