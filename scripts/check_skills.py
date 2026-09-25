#!/usr/bin/env python3
"""Repository checks for claude-ignition-skills.

Checks:
  1. Every .claude/skills/<name>/SKILL.md has valid frontmatter: `name` matching
     the folder, a `description` under 200 characters, the line
     `Applies to: Ignition 8.3.x`, and a references/ folder.
  2. Every relative link in a Markdown file points to a file that exists.
  3. No em-dash characters in repo text files (CLAUDE.md rule).
  4. No 8.1-only wording outside migration context (skip with --allow-81,
     used on the release/8.1 branch).

Exit code is non-zero when any check fails.
"""
import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SKILLS_DIR = os.path.join(ROOT, '.claude', 'skills')
TEXT_EXT = ('.md', '.py', '.json', '.yml', '.yaml', '.sample', '.txt')
SKIP_DIRS = {'.git', 'node_modules', '.venv'}
DESCRIPTION_MAX = 200
APPLIES_TO = 'Applies to: Ignition 8.3.x'
EM_DASH = u'—'

# Files allowed to talk about 8.1 freely (upgrade and history records).
# Any file with 'migration' in its path is also allowed.
ALLOW_81_FILES = {
    'docs/upgrade-notes.md',
    'docs/verification.md',
    'scripts/check_skills.py',
}
# A line mentioning 8.1 is fine when it is clearly about migration or history,
# or compares 8.1 with 8.3 on the same line.
MIGRATION_CONTEXT = re.compile(
    r'8\.1\s*(to|->|→)\s*8\.3|from 8\.1|release/8\.1|v8\.1-final|'
    r'upgrad|migrat|\bin 8\.1|\bon 8\.1|8\.1 branch|8\.3',
    re.IGNORECASE)
VERSION_81 = re.compile(r'(?<![\d.])8\.1(?![\d])')
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, '/')


def walk_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(TEXT_EXT) or name == '.gitignore':
                yield os.path.join(dirpath, name)


def parse_frontmatter(text):
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---', 4)
    if end == -1:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', line)
        if m:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]
            fields[m.group(1)] = value
    return fields


def check_skills(errors):
    if not os.path.isdir(SKILLS_DIR):
        errors.append('missing .claude/skills directory')
        return
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, name)
        if not os.path.isdir(skill_dir):
            continue
        path = os.path.join(skill_dir, 'SKILL.md')
        if not os.path.isfile(path):
            errors.append('%s: missing SKILL.md' % rel(skill_dir))
            continue
        with open(path) as f:
            text = f.read()
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append('%s: missing or malformed frontmatter' % rel(path))
            continue
        if fm.get('name') != name:
            errors.append('%s: frontmatter name %r does not match folder %r'
                          % (rel(path), fm.get('name'), name))
        desc = fm.get('description', '')
        if not desc:
            errors.append('%s: missing description' % rel(path))
        elif len(desc) >= DESCRIPTION_MAX:
            errors.append('%s: description is %d characters (limit %d)'
                          % (rel(path), len(desc), DESCRIPTION_MAX))
        if APPLIES_TO not in text:
            errors.append('%s: missing line %r' % (rel(path), APPLIES_TO))
        if not os.path.isdir(os.path.join(skill_dir, 'references')):
            errors.append('%s: missing references/ folder' % rel(skill_dir))


def check_links(path, text, errors):
    in_code = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        for target in LINK.findall(line):
            if re.match(r'^[a-z]+:', target) or target.startswith('#'):
                continue
            target = target.split('#', 1)[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                errors.append('%s:%d: broken link %s' % (rel(path), lineno, target))


def check_text(path, text, allow_81, errors):
    r = rel(path)
    for lineno, line in enumerate(text.splitlines(), 1):
        if EM_DASH in line and r != 'scripts/check_skills.py':
            errors.append('%s:%d: em-dash found (use " - ")' % (r, lineno))
        if (not allow_81 and r not in ALLOW_81_FILES and 'migration' not in r
                and VERSION_81.search(line)):
            if not MIGRATION_CONTEXT.search(line):
                errors.append('%s:%d: 8.1-only wording: %s' % (r, lineno, line.strip()[:120]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--allow-81', action='store_true',
                        help='skip the 8.1 wording check (release/8.1 branch)')
    args = parser.parse_args()

    errors = []
    check_skills(errors)
    for path in walk_files():
        with open(path, encoding='utf-8') as f:
            text = f.read()
        if path.endswith('.md'):
            check_links(path, text, errors)
        check_text(path, text, args.allow_81, errors)

    for e in errors:
        print(e)
    print('%d problem(s) found' % len(errors))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
