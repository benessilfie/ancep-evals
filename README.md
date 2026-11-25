# An eval set to grade AI on commercial insurance submissions

Ten submissions with the right answers written down first, three Claude models, three runs
each. What I grade is the record the model filed, not the summary it wrote about filing it.

## What broke

One submission beat every model on every run.

The signed application has the no claims box ticked. The two loss runs attached to the same
email show two claims worth $42,000 between them.

All nine runs filed 2 claims, which is the right number, cited the loss runs honestly, and
raised no query. Not one of them put the contradiction in the record.

Opus wrote this in its own notes on the run:

> Application Loss History section has 'CHK HERE IF NONE' ticked, but both carrier loss runs
> and the broker email disclose 2 claims (12,000 property water damage closed; 30,000
> incurred GL bodily injury open). Loss fields taken from loss runs. Treated as an
> inconsistency, not misrepresentation, since the broker disclosed the claims; recommend
> broker obtain a corrected signed application.

So it saw it, diagnosed it correctly and prescribed the right fix. Then it filed the clean
number with 100% of values right and 100% of citations holding up.

Read the transcript and you would pass that run. Read the record and the problem is gone,
and nothing downstream knows to go back for a corrected application. That is the whole
argument for grading the record.

## The rest of it

| model | passed |
| --- | --- |
| Opus 5.5 | 27/30 |
| Sonnet 5.5 | 22/30 |
| Haiku 5.5 | 23/30 |

Sonnet got the derived total wrong on all three runs and wrong differently each time,
8,010,000 then 8,200,000 then 8,800,000 against a real total of 8,400,000. It declared each
time that it had summed the schedule rather than read a stated figure, which is what made
the error findable at all. Honest provenance did not stop the mistake, it made it checkable.

| case | passed |
| --- | --- |
| 05 form contradicts the loss runs | 0/9 |
| 06 total stated nowhere | 6/9 |
| 03 nil losses, letter attached | 7/9 |
| 10 resent with a change | 7/9 |
| 01 clean baseline | 8/9 |
| 02 total stated in the email | 8/9 |

Ninety runs over ten cases is not enough to rank three models, so the per-model numbers are
there for completeness and not as a leaderboard. The per-case numbers are the interesting
ones.

## How the cases are made

The usual way is to take real submissions and pay someone who knows insurance to mark up the
right answers, which takes days and expertise I do not have. I did it the other way round
and write the truth record first, then generate the documents out of it, so the answer key
comes free and a new case takes minutes.

An adversarial case is one deliberate break in the generated documents. The truth record
still holds the right answer, and for a conflict that answer is "raise this with a human"
rather than a value.

Three of the ten have nothing wrong with them. Without those, a model that queried
everything would score full marks, which is a smoke alarm that goes off all day. One of the
clean three is a genuine nil loss history with the carrier's letter attached, and it looks
almost identical to the one where the loss runs are simply missing. Those two need opposite
answers.

## What gets checked

Every answer carries where it came from, which document and whether the model read the value
off the page or worked it out. I check that claim against the document it named, so a model
that sums the schedule and says it read the total off the application fails even when the
number is right.

Most of the checks need no answer key at all:

- paid plus outstanding has to equal incurred
- a stated total has to equal the sum of its rows
- a figure the model says it read has to actually appear in the document it cited
- a value cited to a document that is not in the packet is a false receipt

Those hold for any submission, including one nobody has prepared an answer for, which is the
half of this you could point at real traffic. They live in `src/submission_evals/checks.py`
and take the record and the raw document text, never the truth record.

The grader also has to survive the model phrasing a correct answer differently every run.
Output shape is fixed by a strict JSON schema, so the model fills twenty one named fields and
cannot hand back prose. Content is then compared through normalisers, so `$8,400,000` and
`8400000` match, `Meridian Mutual` and `Meridian Mutual Insurance Company` match, and a model
that honestly declares `derived` where I expected `read` passes, because under-claiming is
not a failure. Three of my early red results were the grader being brittle rather than the
model being wrong, including one that failed Haiku for being honest.

Citation checking is the point rather than a nicety. Correctness and faithfulness come apart
in practice, and
[Correctness is not Faithfulness in RAG Attributions](https://arxiv.org/abs/2412.18004)
measures up to 57% of citations being unfaithful while the answer itself is right.

## The cases

| | case | what it tests |
| --- | --- | --- |
| 01 | clean baseline | nothing wrong |
| 02 | total stated in the email | nothing wrong |
| 03 | nil losses, letter attached | nothing wrong |
| 04 | stale figure in the thread | superseded value |
| 05 | form contradicts the loss runs | documents conflict |
| 06 | total stated nowhere | no stated total |
| 07 | mislabelled paid column | arithmetic does not close |
| 08 | location split across pages | row split by layout |
| 09 | loss runs missing | evidence absent |
| 10 | resent with a change | already on file |

Each one stands for a class of failure rather than a particular bakery, so the next
submission that arrives with its documents in conflict is already covered.

## What this does not show

The documents are synthetic. They show that a failure like this can happen and can be caught,
not how often it happens on real traffic.

The forms use real ACORD field names as data labels but are not ACORD forms, which are
licensed.

I do not work in insurance. Every answer I marked correct carries a link to the source I took
it from, so the expectations are arguable and I would rather be told they are wrong.

## Running it

Needs Python 3.13 and [uv](https://docs.astral.sh/uv/). Put an `ANTHROPIC_API_KEY` in `.env`.

```
uv sync
uv run pytest
```

Nothing above costs money. The results in `results/` are committed, so this re-grades all
ninety runs from the saved transcripts without calling a model:

```
uv run submission-evals regrade
uv run submission-evals summarise
```

To run the models yourself, which does cost money, about 6 cents a run on Haiku and 45 on
Opus:

```
uv run submission-evals run --model claude-haiku-5-5 --effort medium --reps 3
```

For the browser version, the service and the client:

```
uv run uvicorn submission_evals.server:app --port 8000
cd client && npm install && npm run dev
```
