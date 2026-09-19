---
name: ai-prose-scanner
description: >-
  Scan writing for telltale signs of AI-generated prose before sending or
  publishing it. Use this whenever the user wants text checked for "AI tells",
  asks "does this sound AI?" or "can you make this sound more human", or is
  about to send or publish an email, essay, cover letter, blog post, commit
  message, README, PR description, or any prose where sounding human matters.
  Also run it proactively right after you (Claude) draft substantive prose for
  the user, since a scan costs almost nothing and catches the common giveaways.
  It reports em-dashes and en-dashes, semicolons, markdown-formatting tells
  (bold, italic, bolded bullet labels, arrow glyphs like the literal -> and =>),
  a curated AI tell-word list, the "not just X, it is Y" pattern, mid-sentence
  Title Case runs, and length and parenthetical-density stats, all with line
  numbers so the writer can fix issues directly.
---

# AI-prose scanner

Catches the most common telltale signs of AI-generated writing. A scanner pass
before delivery costs almost nothing and catches frequent mistakes: the em-dash
habit, "robust" used as filler, "Furthermore," opening every other paragraph,
the "It's not just X, it's Y" construction, and the arrow glyphs and bolded
labels that make text read like a generated document.

## When to run it

Run this whenever someone wants writing checked for AI artifacts, and run it
proactively whenever you have just produced a substantive piece of prose for the
user. Commit messages, PR descriptions, and READMEs count too: those are exactly
the places a human reviewer is most likely to notice machine cadence.

## How to run it

The scanner is a single Python script with no dependencies. Save the target text
to a file and run it:

```bash
python3 scripts/scan.py path/to/draft.txt
```

Any Python on hand works (`python`, `python3`, or a project interpreter). To
check a commit message or other text you are about to ship, write it to a temp
file first, then scan that file.

It reports:

- Punctuation tells: counts of em-dashes, en-dashes, and semicolons.
- Formatting tells: bold and italic emphasis, bolded bullet labels, arrow
  glyphs, and markdown headings. These are the signals that make text look
  generated, and word lists miss them.
- AI tell-words: counts and line numbers for a curated list of words and
  phrases, grouped as cliches, corporate filler, hedge words, enthusiasm
  tropes, stiff phrasing, and AI-favored connectives.
- The "not just X, it's Y" pattern.
- Mid-sentence Title Case runs, the "overly proper" tell.
- Length stats: word and sentence counts, sentence-length spread, and
  parenthetical density.

## How to read the results

Zero punctuation and formatting tells is the bar. Em-dashes, semicolons, arrow
glyphs, and bolded labels are the strongest single signals, so fix those before
touching anything else.

Tell-words need judgment. Some are correct in their domain: "robust" is the
right word in "adversarially-robust", and "comprehensive" may be right in a tax
memo. The scanner flags; the writer decides whether each flag is a real tell or
a domain term.

High parenthetical density, more than two or three per 300 words, often signals
AI authorship, so rewrite parentheticals into separate sentences. Monotone
sentence length, everything 18 to 22 words with no short punchy ones, is another
tell, so vary sentence length on purpose. The "not just X, it's Y" pattern is
almost always a tell; rewrite it directly.

A clean scan is not proof of good writing. It is proof that the obvious robotic
giveaways are gone.

## What it does not catch

Tone mismatches, generic enthusiasm that resists word lists ("This presents a
unique opportunity to..."), excessive parallel structure, AI hedging ("It's
worth noting that"), and repeated phrasings across paragraphs. For those, read
it again by hand. The scanner is a first filter, not a guarantee.

## Customizing the lists

The word and pattern lists live at the top of `scripts/scan.py`, in the
`WORD_TELLS`, `FORMATTING_TELLS`, and `PUNCT_TELLS` definitions. The script is
written to be read and edited, not treated as a black box. To ban a word you
never want to see, add it to `WORD_TELLS`. If a check produces too many false
positives for a particular kind of writing, loosen its regex or drop it.

## Iterating on a draft

1. Write a draft and save it to a file.
2. Run the scanner.
3. Fix the flagged items, or justify keeping each one.
4. Re-scan.
5. Repeat until it is clean enough to send.
