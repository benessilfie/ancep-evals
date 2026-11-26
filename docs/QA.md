# Manual QA pass

The app runs at http://localhost:5173. A FastAPI service on http://127.0.0.1:8000 backs the
live demo. Both have to be running.

It is an eval set that grades Claude models on commercial insurance submissions. Twelve
packets of documents, three models, three runs each, 108 recorded results. Three tabs: Start
here, Live demo, Findings.

Work through this at three widths: a phone around 390px, a tablet around 820px, and a desktop
window around 1400px. Most of what broke last night only broke at one of them.

## Start here

- [ ] Opens on this tab by default
- [ ] Six steps, Back and Next move between them
- [ ] Desktop and tablet show the numbered chip row with a dark marker that slides between
      chips rather than jumping
- [ ] Phone hides the chips and shows `STEP 3 OF 6` above the step title instead
- [ ] Phone pins Back and Next to the bottom of the screen on every step, including step 6
      where the content is short. They must not float mid-screen
- [ ] Desktop and tablet keep Back and Next in the same vertical position on all six steps
- [ ] Step 1 lists twelve submissions, each tagged with a failure class
- [ ] Step 5 shows the contradiction panel for packet 05
- [ ] Step 6 buttons jump to Live demo and Findings

## Live demo

- [ ] Model picker shows Haiku, Sonnet, Opus and nothing else. No counts, no prices, no limits
- [ ] Packet dropdown lists all twelve, including `11 London market slip` and
      `12 No FEIN exists`
- [ ] Documents tab lists the packet's documents. Desktop shows a sidebar list, phone shows a
      dropdown switcher with `document 3 of 8` underneath
- [ ] **Packets 11 and 12 contain a `Market reform slip` document. Open it.** This has never
      been seen on screen. Check the name, the icon, and that the text is not cut off
- [ ] Changing packet clears any previous result and returns to `Nothing has run yet`, staying
      on the Verdict tab
- [ ] Phone shows the controls and the content as two separate cards on a recessed background,
      not one continuous scroll
- [ ] Run history is collapsed on a phone, open on tablet and desktop

### Running one

Picking Haiku keeps it cheap. Packet 05 is the interesting one.

- [ ] A spinner appears on the active stage and a clock ticks in tenths. The page must not look
      frozen
- [ ] Before any field arrives it says `usually 25 to 45 seconds`
- [ ] Fields fill in one at a time, wiping in from the left rather than popping
- [ ] A verdict card appears at the end with `what this packet tests` and `what should happen`
- [ ] The verdict copy describes the packet you actually ran
- [ ] The run appears in `your runs`, and clicking it restores that result

## Findings

- [ ] Desktop shows the packet list on the left, phone shows a dropdown
- [ ] Twelve packets. Packet 05 should show `0/9`
- [ ] Selecting a packet moves the indicator smoothly and resets the run selector
- [ ] Run buttons line up in a grid under Opus, Sonnet and Haiku
- [ ] The verdict panel says `eval result` above a large Passed or Failed
- [ ] `what the model said about this packet` opens and closes smoothly
- [ ] The row above the document reads `output` on the left and a dropdown on the right, on one
      line, never wrapping
- [ ] **Open packet 11 and pick Sonnet run 2.** The record should show `total sum insured`
      raised for a human, and the model's own note should say the figures match and it is not a
      conflict. That contradiction is a finding, not a bug
- [ ] Header shows the title on the left and the tabs centred. Stats on the right only appear
      on Findings and only on a wide screen

## Things that broke before

Worth re-checking, since each took more than one attempt.

- [ ] Document tabs overlapping the content below them, at any width
- [ ] Any control with a heavy blue or black focus box instead of a quiet underline
- [ ] Any dark button turning blue on hover rather than lightening
- [ ] Horizontal scrolling anywhere on a phone
- [ ] A stale result from a previous packet still on screen after switching

## Reporting back

For anything wrong, say which tab, which width, and what you expected instead. A screenshot
beats a description.
