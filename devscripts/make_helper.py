import argparse
import json
import logging
import sys
from pathlib import Path

from devscripts.make_changelog import CommitRange, LOCATION_PATH, get_contributors
from devscripts.utils import read_file, run_process


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='helper script for generating ')
parser.add_argument(
    '-v', '--verbosity', action='count', default=0,
    help='increase verbosity (can be used twice)')
subparsers = parser.add_subparsers(help='commands', dest='command')

parser = subparsers.add_parser('authors', help='List the authors from a git commit range')
parser.add_argument(
    'commitish', default='2c736b4f6180a7c0554a5893f16bb65be909e182', nargs='?',
    help='The first commit where "Authored by: " was used')
parser.add_argument(
    '--no-override', action='store_true',
    help='skip override json in commit generation (default: %(default)s)')
parser.add_argument(
    '--override-path', type=Path, default=LOCATION_PATH / 'changelog_override.json',
    help='path to the changelog_override.json file')
parser.add_argument(
    '--default-author', default='pukkandan',
    help='the author to use without a author indicator (default: %(default)s)')

parser = subparsers.add_parser('clean', help='List the authors from a git commit range')
parser.add_argument(
    'part', help='which part to clean')

args = parser.parse_args()
logging.basicConfig(
    datefmt='%Y-%m-%d %H-%M-%S', format='{asctime} | {levelname:<8} | {message}',
    level=logging.WARNING - 10 * args.verbosity, style='{', stream=sys.stderr)

commits = CommitRange(args.commitish, 'HEAD', 'pukkandan')
if not args.no_override:
    if args.override_path.exists():
        overrides = json.loads(read_file(args.override_path))
        commits.apply_overrides(overrides)
    else:
        logger.warning(f'File {args.override_path.as_posix()} does not exist')

authors = get_contributors(commits)
folded_authors = set(map(str.casefold, authors))

mailmap = {}
output = run_process('git', 'log', 'HEAD', '--format=%aN|%aE').stdout
for line in output.splitlines():
    author, mail = line.split('|')
    if mail not in mailmap:
        mailmap[mail] = author

output = run_process('git', 'log', args.commitish, '--format=%aE').stdout
for author in map(mailmap.__getitem__, output.splitlines()):
    folded_author = author.casefold()
    if folded_author not in folded_authors:
        folded_authors.add(folded_author)
        authors.append(author)

print('\n'.join(sorted(authors, key=str.casefold)))
