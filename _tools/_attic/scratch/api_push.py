"""Push local commits through api.github.com, for when github.com:443 is unreachable.

The git host and the API host are different names and they do not fail together:
on this machine `api.github.com` answers in 0.4 s while `github.com:443` times
out.  So when `git push` cannot connect, the same commits can still be written
through the Git Data API.

This is not a different commit -- it rebuilds each LOCAL commit's tree object on
the server, and asserts the server's tree sha equals the local one.  A git tree
sha hashes the entries plus their blob shas, so a match is proof the server tree
is byte-identical, not merely similar.

It pushes a RANGE, not just HEAD.  The first version took one commit, which was
fine until the network stayed down across three of them -- and the obvious
workaround, checking out each commit in turn, is a series of writes to a history
that is already ahead of the server.  Walking the range with the same tree guard
per step costs nothing extra and never moves the working tree.

Which commits are in the range is decided by CONTENT, not by `origin/main`: the
local remote-tracking ref is stale exactly when this script is needed.  We walk
back from HEAD until a commit's tree matches the server's current tree, and push
whatever sits after it.

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


def remote_tip():
    r = json.loads(gh('api', 'repos/%s/commits/main' % REPO))
    return r['sha'], r['commit']['tree']['sha']


def server_sha_for_tree(tree):
    """The newest local commit whose tree is `tree`, or None.

    Matching on the tree rather than the commit sha is deliberate: GitHub
    re-authors commits created through this endpoint (DECISIONS 143), so a
    commit that has already gone out this route comes back content-identical
    and object-different.  A sha comparison would fail to find it, decide the
    whole history is unpushed, and then refuse at the first guard -- or worse,
    try to push commits that are already there.
    """
    for line in git('rev-list', 'HEAD').splitlines():
        sha = line.strip()
        if not sha:
            continue
        if git('rev-parse', '%s^{tree}' % sha).strip() == tree:
            return sha
    return None


def push_one(rev, remote_sha, expect_tree):
    """Put local commit `rev` on top of server commit `remote_sha`.

    The guard compares TREES.  What has to hold is that the commit being added
    sits on top of the content that is already on the server, and tree equality
    states exactly that.
    """
    local_tree = git('rev-parse', '%s^{tree}' % rev).strip()
    parent = git('rev-parse', '%s^' % rev).strip()
    parent_tree = git('rev-parse', '%s^{tree}' % parent).strip()
    if expect_tree != parent_tree:
        sys.exit('%s was built on tree %s but the server is at %s -- refusing '
                 'to rewrite somebody else\'s history'
                 % (rev[:8], parent_tree[:8], expect_tree[:8]))

    message = git('log', '-1', '--pretty=%B', rev)
    # --name-status, not --name-only: a deletion has no blob to read at all.
    status = [ln.split('\t') for ln in
              git('diff', '--name-status', parent, rev).splitlines() if ln.strip()]
    entries = []
    for parts in status:
        kind, names = parts[0][0], parts[1:]
        # A rename is a write at the new path AND a delete at the old one.
        # Emitting only the new path leaves the old blob in the base tree, so
        # the rebuilt tree would hold both and the equality guard would fail.
        plan = ([('R', names[1], True), ('R', names[0], False)]
                if kind == 'R' else [(kind, names[0], kind != 'D')])
        for code, rel, alive in plan:
            path = rel.replace('\\', '/')
            if not alive:
                entries.append({'path': path, 'mode': '100644',
                                'type': 'blob', 'sha': None})
                print('  del           %s' % rel)
                continue
            # From the COMMIT, never from the worktree.  The worktree holds
            # whatever is checked out -- i.e. HEAD -- so pushing anything else
            # uploads HEAD's bytes under an older commit's tree, and the guard
            # fails with a size difference that is really an off-by-one in
            # "which version am I looking at".  This went unnoticed while the
            # script only ever pushed HEAD.
            data = subprocess.run(['git', 'cat-file', 'blob', '%s:%s' % (rev, rel)],
                                  cwd=ROOT, capture_output=True, check=True).stdout
            blob = gh_json('POST', 'repos/%s/git/blobs' % REPO, {
                'content': base64.b64encode(data).decode('ascii'),
                'encoding': 'base64',
            })
            entries.append({'path': path, 'mode': '100644', 'type': 'blob',
                            'sha': blob['sha']})
            print('  %s %s  %s' % (code, blob['sha'][:8], rel))

    tree = gh_json('POST', 'repos/%s/git/trees' % REPO,
                   {'base_tree': expect_tree, 'tree': entries})
    if tree['sha'] != local_tree:
        sys.exit('server tree %s != local tree %s for %s -- the blobs did not '
                 'reproduce the local commit, nothing was committed'
                 % (tree['sha'], local_tree, rev[:8]))
    print('  server tree   %s  (== local tree)' % tree['sha'][:8])

    commit = gh_json('POST', 'repos/%s/git/commits' % REPO, {
        'message': message, 'tree': tree['sha'], 'parents': [remote_sha],
    })
    print('  server commit %s' % commit['sha'][:8])
    gh_json('PATCH', 'repos/%s/git/refs/heads/main' % REPO,
            {'sha': commit['sha'], 'force': False})
    return commit['sha'], tree['sha']


def main():
    remote_sha, remote_tree = remote_tip()
    print('server main   %s  tree %s' % (remote_sha[:8], remote_tree[:8]))

    found = server_sha_for_tree(remote_tree)
    if found is None:
        sys.exit('no local commit has tree %s -- the server and this checkout '
                 'do not share content, refusing to guess' % remote_tree[:8])
    todo = git('rev-list', '--reverse', '%s..HEAD' % found).split()
    local_head = git('rev-parse', 'HEAD').strip()
    local_tree = git('rev-parse', 'HEAD^{tree}').strip()
    print('  %s is already on the server (by content); %d commit(s) to send'
          % (found[:8], len(todo)))

    for rev in todo:
        print('%s' % git('log', '-1', '--pretty=%h %s', rev).strip())
        remote_sha, remote_tree = push_one(rev, remote_sha, remote_tree)
        print('  refs/heads/main -> %s' % remote_sha[:8])

    if todo and remote_tree != local_tree:
        sys.exit('server tree %s but HEAD is %s -- the range did not reproduce '
                 'the local tip' % (remote_tree[:8], local_tree[:8]))
    print('done: server main is HEAD (%s), tree matches'
          % local_head[:8])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
