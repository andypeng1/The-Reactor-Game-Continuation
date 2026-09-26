"""Push every unpushed local commit through api.github.com.

`api_push.py` handles exactly one commit on top of the remote tip.  That was
right for the push it was written for and wrong for the next one: two commits
had accumulated locally while `github.com:443` was unreachable, and the
one-commit script would have refused to run against a base it did not recognise.

The git host and the API host are different names and they do not fail together:
on this machine `api.github.com` answers in well under a second while
`github.com:443` times out.  So when `git push` cannot connect, the same commits
can still be written through the Git Data API.

This is not a different history.  It rebuilds each LOCAL commit's tree object on
the server and asserts the server's tree sha equals the local one.  A git tree
sha is a hash of the entries plus their blob shas, so a match is proof the server
tree is byte-identical, not merely similar.

Two things the one-commit version did not have to handle and this one does:

  * DELETIONS.  A path that is gone at a given commit is sent as a tree entry
    with `sha: null`; sending only the existing files would re-add what the
    commit removed, and the tree sha check would catch exactly that.
  * PARTIAL PUSHES.  Every blob, tree and commit object is created first and the
    ref is moved LAST, once.  A failure halfway through leaves orphaned objects
    and an unmoved branch, which is the failure you can recover from; moving the
    ref per commit leaves a history that is half yours.

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


def gh(*args):
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


def changed_paths(commit, parent):
    """Paths this commit differs from its parent in, deletions included.

    `-z` and a NUL split rather than line splitting: git quotes paths that
    contain non-ASCII by default, and a quoted path is not a path."""
    raw = subprocess.run(
        ['git', 'diff', '--name-only', '-z', parent, commit],
        cwd=ROOT, capture_output=True, check=True).stdout
    return [p.decode('utf-8') for p in raw.split(b'\0') if p]


def exists_in(commit, path):
    return subprocess.run(['git', 'cat-file', '-e', '%s:%s' % (commit, path)],
                          cwd=ROOT, capture_output=True).returncode == 0


def main():
    # The /git/commits/ endpoint wants a sha, not a ref name -- asking it for
    # "main" is a 404, not a fallback.  The plain /commits/ endpoint does accept
    # a ref, and nests the tree one level deeper.
    remote = json.loads(gh('api', 'repos/%s/commits/main' % REPO))
    tip = remote['sha']
    tip_tree = remote['commit']['tree']['sha']
    print('remote main   %s  tree %s' % (tip[:8], tip_tree[:8]))

    # Walk back from HEAD collecting what the remote does not have.  The stop
    # condition compares TREES as well as shas, because a commit that has gone
    # out this way is content-identical but not the same object -- GitHub
    # re-authors it (DECISIONS 143) -- so a sha test alone would walk past the
    # remote tip and try to push the whole history.
    chain = []
    cursor = 'HEAD'
    while True:
        sha = git('rev-parse', cursor).strip()
        tree = git('rev-parse', '%s^{tree}' % cursor).strip()
        if sha == tip or tree == tip_tree:
            print('  stopped at %s (already on the remote)' % sha[:8])
            break
        chain.append(sha)
        if git('rev-list', '--parents', '-n', '1', sha).split().__len__() < 2:
            sys.exit('ran out of parents before reaching the remote tip -- '
                     'these histories are unrelated; refusing to rewrite')
        cursor = git('rev-parse', '%s^' % sha).strip()
    chain.reverse()
    if not chain:
        print('nothing to push')
        return 0
    print('  %d commit(s) to push: %s'
          % (len(chain), ', '.join(c[:8] for c in chain)))

    # Every object first, the ref last.  See PARTIAL PUSHES in the docstring.
    base_tree = tip_tree
    parent = tip
    for sha in chain:
        subject = git('log', '-1', '--pretty=%s', sha).strip()
        message = git('log', '-1', '--pretty=%B', sha)
        # Diffed against the commit's LOCAL parent, not the server commit just
        # created.  The two are the same content by construction -- the tree
        # check below is what proves it -- but the server sha is an object this
        # repository does not have, so it cannot be handed to `git diff`.
        paths = changed_paths(sha, git('rev-parse', '%s^' % sha).strip())
        entries = []
        for rel in paths:
            if exists_in(sha, rel):
                data = subprocess.run(['git', 'show', '%s:%s' % (sha, rel)],
                                      cwd=ROOT, capture_output=True,
                                      check=True).stdout
                blob = gh_json('POST', 'repos/%s/git/blobs' % REPO, {
                    'content': base64.b64encode(data).decode('ascii'),
                    'encoding': 'base64',
                })
                entries.append({'path': rel.replace('\\', '/'),
                                'mode': '100644', 'type': 'blob',
                                'sha': blob['sha']})
            else:
                # Deletion: an entry with a null sha is the API's "remove this".
                entries.append({'path': rel.replace('\\', '/'),
                                'mode': '100644', 'type': 'blob', 'sha': None})
        tree = gh_json('POST', 'repos/%s/git/trees' % REPO,
                       {'base_tree': base_tree, 'tree': entries})
        local_tree = git('rev-parse', '%s^{tree}' % sha).strip()
        if tree['sha'] != local_tree:
            sys.exit('server tree %s != local tree %s for %s (%s) -- the blobs '
                     'did not reproduce the commit, ref not moved'
                     % (tree['sha'][:8], local_tree[:8], sha[:8], subject))
        commit = gh_json('POST', 'repos/%s/git/commits' % REPO, {
            'message': message, 'tree': tree['sha'], 'parents': [parent],
        })
        print('  %s -> %s  %s' % (sha[:8], commit['sha'][:8], subject))
        base_tree = tree['sha']
        parent = commit['sha']

    gh_json('PATCH', 'repos/%s/git/refs/heads/main' % REPO,
            {'sha': parent, 'force': False})
    print('refs/heads/main -> %s' % parent[:8])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
