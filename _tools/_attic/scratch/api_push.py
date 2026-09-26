"""Push one commit through api.github.com, for when github.com:443 is unreachable.

The git host and the API host are different names and they do not fail together:
on this machine `api.github.com` answers in 0.4 s while `github.com:443` times
out.  So when `git push` cannot connect, the same commit can still be written
through the Git Data API.

This is not a different commit -- it rebuilds the LOCAL commit's tree object on
the server, and then asserts the server's tree sha equals the local one
(20c3caba...).  A git tree sha is a hash of the entries plus their blob shas, so
a match is proof the server tree is byte-identical, not merely similar.

Auth comes from `gh`, so no token is handled here.
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

REPO = 'andypeng1/The-Reactor-Game-Continuation'
ROOT = Path(r'D:\rblxTRGproject')
SCRATCH = ROOT / '_tools' / '_attic' / 'scratch'


def git(*args):
    p = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True,
                       check=True)
    return p.stdout.decode('utf-8')


def gh(*args, stdin=None):
    # Bytes, then decode as UTF-8 by hand.  A Chinese Windows console runs the
    # GBK codec, and text=True would use it -- so the first push worked (that
    # message was ASCII) and the second died on the em-dash in the commit being
    # read back.  The payload is UTF-8 regardless of what the console prefers.
    p = subprocess.run(['gh'] + list(args), capture_output=True)
    if p.returncode != 0:
        sys.exit('gh %s failed:\n%s\n%s'
                 % (' '.join(args), p.stdout.decode('utf-8', 'replace'),
                    p.stderr.decode('utf-8', 'replace')))
    return p.stdout.decode('utf-8')


def gh_json(method, endpoint, body):
    """POST/PATCH a JSON body.  Goes through a file because a blob body is
    hundreds of KB and Windows argv tops out around 32 KB."""
    f = SCRATCH / '_api_body.json'
    f.write_text(json.dumps(body), encoding='utf-8')
    out = gh('api', '-X', method, endpoint, '--input', str(f))
    f.unlink()
    return json.loads(out) if out.strip() else {}


def main():
    local_tree = git('rev-parse', 'HEAD^{tree}').strip()
    local_parent = git('rev-parse', 'HEAD~1').strip()
    message = git('log', '-1', '--pretty=%B')
    changed = git('diff', '--name-only', 'HEAD~1', 'HEAD').split()
    print('local commit  %s' % git('rev-parse', '--short', 'HEAD').strip())
    print('  tree        %s' % local_tree)
    print('  parent      %s' % local_parent)
    print('  %d changed paths' % len(changed))

    # The /git/commits/ endpoint wants a sha, not a ref name -- asking it for
    # "main" is a 404, not a fallback.  The plain /commits/ endpoint does accept
    # a ref, and nests the tree one level deeper.
    #
    # The guard compares TREES, not shas.  Once a commit has gone out this way
    # the remote tip and the local tip are content-identical but not the same
    # object (GitHub re-authors it, see DECISIONS 143), so a sha comparison would
    # refuse to push a second time for no real reason.  What actually has to hold
    # is that the commit being added sits on top of the content that is already
    # there -- and tree equality states exactly that.
    remote = json.loads(gh('api', 'repos/%s/commits/main' % REPO))
    base_tree = remote['commit']['tree']['sha']
    parent_tree = git('rev-parse', 'HEAD~1^{tree}').strip()
    if base_tree != parent_tree:
        sys.exit('remote tree %s but the local commit was built on %s -- '
                 'refusing to rewrite somebody else\'s history'
                 % (base_tree, parent_tree))
    if remote['sha'] != local_parent:
        print('  (remote tip %s is not the local parent %s, but the trees '
              'match -- content-identical, see DECISIONS 143)'
              % (remote['sha'][:8], local_parent[:8]))
    print('remote main   %s  (tree matches the local parent)' % remote['sha'][:8])

    entries = []
    for rel in changed:
        data = (ROOT / rel).read_bytes()
        blob = gh_json('POST', 'repos/%s/git/blobs' % REPO, {
            'content': base64.b64encode(data).decode('ascii'),
            'encoding': 'base64',
        })
        entries.append({'path': rel.replace('\\', '/'), 'mode': '100644',
                        'type': 'blob', 'sha': blob['sha']})
        print('  blob %s  %s' % (blob['sha'][:8], rel))

    tree = gh_json('POST', 'repos/%s/git/trees' % REPO,
                   {'base_tree': base_tree, 'tree': entries})
    if tree['sha'] != local_tree:
        sys.exit('server tree %s != local tree %s -- the blobs did not '
                 'reproduce the local commit, nothing was committed'
                 % (tree['sha'], local_tree))
    print('server tree   %s  (== local tree)' % tree['sha'][:8])

    commit = gh_json('POST', 'repos/%s/git/commits' % REPO, {
        'message': message, 'tree': tree['sha'], 'parents': [remote['sha']],
    })
    print('server commit %s' % commit['sha'][:8])

    gh_json('PATCH', 'repos/%s/git/refs/heads/main' % REPO,
            {'sha': commit['sha'], 'force': False})
    print('refs/heads/main -> %s' % commit['sha'][:8])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
