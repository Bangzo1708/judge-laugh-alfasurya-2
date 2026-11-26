#!/usr/bin/env python3
"""Judge Laugh (replacement round) -- pick the strongest one-line office joke.

Deterministic by design: no randomness, no clock, no network, no file reads.
Three hand-written candidates are scored 0-5 against the judge's five
criteria, in the judge's own order of importance:

  1. It is about office life and lands as a joke.
  2. The observation is true to the office (listener nods before laughing).
  3. The turn is surprising: a fresh angle or an unexpected last word.
  4. It is tight: one line, no wasted setup, reads cleanly aloud.
  5. It is original: not a familiar line with the nouns swapped.

The winner is the highest total; a tie is broken by the earliest criterion
where the tied candidates differ (criterion 1 first, then 2, 3, 4, 5),
exactly mirroring how the judge weighs the criteria. Any tie left after
that keeps the candidate listed first.

The winning joke is written to /output/entry.txt (or $ENTRY_OUTPUT when
set), then read back and checked byte-for-byte against the intended text.
Gate: UTF-8, 1-200 characters, a single line, not only whitespace.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Candidates. Each one is a different angle, and none of them touches the
# old entry's theme (an AI summarising a meeting) or the banned stock lines:
# no "per my last email", no "reply all", no "meeting that should have been
# an email", no broken printer, no empty coffee pot, no stale pun.
# ---------------------------------------------------------------------------

CANDIDATES = [
    {
        "id": "focus-time",
        "angle": "calendar / focus time invaded by other people's meetings",
        "text": (
            "I blocked an hour for focus time and my calendar invited "
            "six people to watch me do it."
        ),
        # Scores per criterion, in the judge's order (1-5 above).
        "scores": (5, 5, 4, 4, 4),
        "reasons": (
            # 1. About office life, lands as a joke.
            "Unmistakably office life, and the punchline turns it into a joke.",
            # 2. True observation.
            "Focus-time blocks really do get steamrolled by other people's invites.",
            # 3. Surprising turn.
            "The calendar 'inviting six people to watch' is a fresh image, "
            "not a stock line.",
            # 4. Tight.
            "One breath, no wasted word, though 'for focus time' is slightly flat.",
            # 5. Original.
            "The calendar-as-host framing is new; the setup is not a known joke.",
        ),
    },
    {
        "id": "out-of-office",
        "angle": "out-of-office auto-reply respected more than the person",
        "text": (
            "My out-of-office reply gets more respect than I do \u2014 "
            "people actually wait for it to come back."
        ),
        "scores": (5, 4, 4, 4, 4),
        "reasons": (
            # 1.
            "Clearly office life, and the comparison is the joke.",
            # 2.
            "People really do honour an OOO reply more than a person saying no; "
            "the 'more respect than I do' stretch costs a point.",
            # 3.
            "'Wait for it to come back' is an unexpected last beat, "
            "but the twist is telegraphed by the setup.",
            # 4.
            "Reads cleanly in one breath; the em dash does the timing work.",
            # 5.
            "The OOO angle is uncommon, but 'respected more than me' is a "
            "familiar self-deprecation shape.",
        ),
    },
    {
        "id": "open-door",
        "angle": "boss's open-door policy as surveillance of who leaves early",
        "text": (
            "My boss has an open-door policy: the door is open so he can "
            "see who's leaving early."
        ),
        "scores": (5, 5, 5, 5, 4),
        "reasons": (
            # 1.
            "Pure office life, and the second half is the joke landing.",
            # 2.
            "Open-door policies are real, and every office worker knows the "
            "boss notices who leaves first -- the nod comes before the laugh.",
            # 3.
            "The setup sounds like praise of the boss, then the last word "
            "flips it into surveillance: genuine misdirection, not a pun.",
            # 4.
            "Every word earns its place; setup and punch share one short "
            "sentence that reads aloud in a single breath.",
            # 5.
            "The open-door phrase itself is familiar, but the twist is not: "
            "the judge has heard open-door praise a thousand times, never "
            "open-door as a clock-watching trap -- and that is why this "
            "candidate beats focus-time, whose punchline the listener can "
            "see coming halfway through the sentence.",
        ),
    },
]

MAX_CHARS = 200
CRITERION_NAMES = (
    "1. office joke that lands",
    "2. true observation",
    "3. surprising turn",
    "4. tight",
    "5. original",
)


def total(scores):
    """Sum of the five criterion scores."""
    return sum(scores)


def pick_winner(candidates):
    """Highest total wins; ties break on the earliest differing criterion.

    The sort key is (-total, -c1, -c2, -c3, -c4, -c5): the candidate that is
    better on the judge's most important criterion wins the tie, and only
    if all five are equal does the earlier-listed candidate stay first
    (Python's sort is stable, and min() keeps the first minimum).
    """
    def key(candidate):
        scores = candidate["scores"]
        return (-total(scores),) + tuple(-s for s in scores)

    return min(candidates, key=key)


def validate_gate(text):
    """The competition gate: UTF-8, 1-200 chars, one line, not blank."""
    if not isinstance(text, str):
        raise ValueError("entry is not text")
    if not (1 <= len(text) <= MAX_CHARS):
        raise ValueError(
            "entry is %d characters, gate requires 1-%d" % (len(text), MAX_CHARS)
        )
    if text.strip() == "":
        raise ValueError("entry is only whitespace")
    if "\n" in text or "\r" in text:
        raise ValueError("entry must be a single line")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        raise ValueError("entry contains a control character")
    text.encode("utf-8")  # raises if not encodable as UTF-8
    return True


def main():
    output_path = os.environ.get("ENTRY_OUTPUT") or "/output/entry.txt"

    print("Candidates (scored 0-5 per criterion, judge's order):")
    for candidate in CANDIDATES:
        print()
        print("  [%s] angle: %s" % (candidate["id"], candidate["angle"]))
        print("  text: %s" % candidate["text"])
        print("  chars: %d" % len(candidate["text"]))
        for name, score, reason in zip(
            CRITERION_NAMES, candidate["scores"], candidate["reasons"]
        ):
            print("    %s: %d -- %s" % (name, score, reason))
        print("  TOTAL: %d / 25" % total(candidate["scores"]))

    winner = pick_winner(CANDIDATES)
    entry = winner["text"]

    print()
    print(
        "Winner: [%s] with %d / 25 (next best: %d)"
        % (
            winner["id"],
            total(winner["scores"]),
            max(total(c["scores"]) for c in CANDIDATES if c is not winner),
        )
    )
    print("Entry (%d chars): %s" % (len(entry), entry))

    validate_gate(entry)

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(entry)

    # Read-back verification: the file on disk must be exactly the entry.
    with open(output_path, "r", encoding="utf-8") as handle:
        written = handle.read()
    if written != entry:
        print("ERROR: read-back mismatch", file=sys.stderr)
        print("  expected: %r" % entry, file=sys.stderr)
        print("  on disk:  %r" % written, file=sys.stderr)
        return 1
    validate_gate(written)

    print("Wrote %s (%d chars), read-back verified." % (output_path, len(written)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
