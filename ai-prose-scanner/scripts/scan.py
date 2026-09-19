#!/usr/bin/env python3
"""Scan a text file for AI-prose tells.

Usage: python3 scan.py <path-to-text-file>

Reports punctuation tells (em-dashes, en-dashes, semicolons), markdown
formatting tells (bold/italic emphasis, bolded bullet labels, arrow glyphs),
AI tell-words and phrases by line number, the "not just X, it's Y" pattern,
mid-sentence Title Case runs (the "overly proper" tell), and length stats.

The lists here are intentionally generous. Some flags will be false positives
(a "robust" in "adversarially-robust" is the correct technical term, not a
tell; a bolded label may be wanted in a README). Use judgment.
"""

import sys
import re

# Punctuation that AI loves and humans rarely use in casual prose.
PUNCT_TELLS = {
    '—': 'em-dash',
    '–': 'en-dash',
    ';': 'semicolon',
}

# Formatting tells: name -> compiled regex. These catch the "it looks like a
# generated document" signals that word lists miss. Counted across the whole
# text; first few line numbers reported.
FORMATTING_TELLS = {
    'bolded bullet label (- **Label:**)': re.compile(r'^\s*[-*+]\s+\*\*[^*]+\*\*\s*:?'),
    'bold emphasis (**...**)': re.compile(r'\*\*[^*\n]+\*\*'),
    'italic/underscore emphasis (*...* or _..._)': re.compile(r'(?<![*\w])[*_][^*_\n]+[*_](?![*\w])'),
    'arrow glyph (->, =>, →, ⇒)': re.compile(r'->|=>|→|⇒|<-'),
    'markdown heading (#)': re.compile(r'^\s{0,3}#{1,6}\s'),
}

# Words and phrases that are statistically over-represented in LLM output.
# Organized roughly by category for readability. Edit freely.
WORD_TELLS = [
    # Cliches
    'delve', 'tapestry', 'navigate', 'realm', 'landscape',
    'unleash', 'unlock', 'foster', 'cultivate', 'embark',
    'underscore', 'paramount', 'multifaceted', 'utmost',
    'commendable', 'meticulous',
    # Corporate filler
    'leverage', 'synergy', 'holistic', 'comprehensive',
    'innovative', 'cutting-edge', 'state-of-the-art', 'scalable',
    'robust',
    # Hedge words from the Anthropic system prompt list
    'genuinely', 'honestly', 'straightforward',
    # Enthusiasm tropes
    'I am thrilled', "I'm thrilled", 'I am excited', "I'm excited to",
    'uniquely qualified', 'perfect fit', 'passionate about',
    'dedicated to', 'committed to',
    # Stiff / overly proper phrasing
    'updated resume', 'in order to', 'as a next step', 'please find attached',
    'I look forward to', 'do not hesitate', 'kindly',
    # AI-favored connectives
    'Furthermore,', 'Moreover,', 'Additionally,',
    'In conclusion', 'In summary', 'In essence',
    # Patterns
    "It's not just", 'It is not just',
    # AI hedging
    "It's worth noting", "It is worth noting",
    "It's important to", "It is important to",
]

# Words that legitimately start a sentence / are proper nouns, so a Title Case
# run beginning with them is less suspicious. Keep small.
TITLECASE_STOP = {'I', 'A', 'The', 'An'}


def find_lines_with(text, needle):
    """Return list of (lineno, line) where needle appears (case-insensitive)."""
    needle_low = needle.lower()
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        if needle_low in line.lower():
            out.append((i, line.strip()))
    return out


def find_lines_regex(text, pattern):
    """Return list of (lineno, line) where the regex matches."""
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            out.append((i, line.strip()))
    return out


def find_titlecase_runs(text):
    """Find runs of 2+ Capitalized words that appear mid-sentence.

    These flag 'overly proper' framing like 'Senior Director of Customer
    Success'. We skip runs at the very start of a line/sentence and
    runs that are mostly known stop-words. Noisy by nature: a soft signal.
    """
    out = []
    # token with position; a run is consecutive Capitalized tokens
    run_re = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,})\b')
    for i, line in enumerate(text.splitlines(), start=1):
        for m in run_re.finditer(line):
            start = m.start()
            # skip if the run starts the line (likely a real heading/sentence)
            prefix = line[:start].strip()
            if prefix == '':
                continue
            # skip if the char right before is sentence-ending punctuation
            if prefix[-1] in '.!?:':
                continue
            phrase = m.group(1)
            words = phrase.split()
            if all(w in TITLECASE_STOP for w in words):
                continue
            out.append((i, phrase))
    return out


def report_section(title, hits, limit=3):
    if hits:
        print(f'  {title}: {len(hits)} occurrence(s)')
        for lineno, line in hits[:limit]:
            preview = line if len(line) <= 100 else line[:97] + '...'
            print(f'      L{lineno}: {preview}')
    return bool(hits)


def main(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()

    print(f'Scanning: {path}\n' + '-' * 60)

    # Punctuation
    pcounts = {}
    for ch, name in PUNCT_TELLS.items():
        c = text.count(ch)
        pcounts[name] = c
        print(f'{name:12s} ({ch}): {c}')

    # Formatting tells
    print('\nFormatting tells (markdown emphasis, bullets, arrows):')
    fmt_found = False
    for name, pattern in FORMATTING_TELLS.items():
        hits = find_lines_regex(text, pattern)
        if report_section(name, hits):
            fmt_found = True
    if not fmt_found:
        print('  (none)')

    # Words and phrases
    print('\nAI tell-words and phrases (case-insensitive substring match):')
    found_any = False
    for word in WORD_TELLS:
        hits = find_lines_with(text, word)
        if report_section(f'"{word}"', hits):
            found_any = True
    if not found_any:
        print('  (none)')

    # Title Case runs
    print('\nMid-sentence Title Case runs (the "overly proper" tell):')
    tc = find_titlecase_runs(text)
    if tc:
        for lineno, phrase in tc[:8]:
            print(f'      L{lineno}: {phrase}')
        if len(tc) > 8:
            print(f'      ... and {len(tc) - 8} more')
    else:
        print('  (none)')

    # "not just X, it's Y" pattern
    notjust = re.findall(r"(?i)not just .{1,40}?,? ?(it'?s|it is|but) ", text)
    if notjust:
        print(f"\n'not just X, it's Y' pattern: {len(notjust)} occurrence(s)")

    # Length stats
    print('\nLength stats:')
    words = text.split()
    sents = [s for s in re.split(r'[.!?]\s+', text) if s.strip()]
    print(f'  Words: {len(words)}')
    if sents:
        lens = [len(s.split()) for s in sents]
        print(f'  Sentences: {len(sents)}')
        print(f'  Sentence length: min {min(lens)}, avg {sum(lens) / len(lens):.1f}, max {max(lens)}')
    parens = text.count('(')
    print(f'  Open parens: {parens}')
    if len(words) > 0:
        ratio = parens / len(words) * 1000
        print(f'  Parens per 1000 words: {ratio:.1f}')

    # Verdict
    print('\n' + '-' * 60)
    total_punct = sum(pcounts.values())
    if total_punct == 0 and not found_any and not fmt_found and not tc:
        print('Clean. No punctuation, formatting, or word tells.')
    elif total_punct == 0 and not fmt_found:
        print('Punctuation and formatting clean. Review flagged words and '
              'Title Case runs and decide which are justified domain terms.')
    else:
        print('Tells present. Punctuation and markdown formatting (em-dashes, '
              'bolded headers, arrow glyphs) are the strongest signals. Fix '
              'those first, then weigh the word and capitalization flags.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: scan.py <path-to-text-file>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
