"""One-shot: PROGRESS 51.6 + DECISIONS 143 + a clause in CLAUDE.md.

Records the second half of Phase 51: the push channel.  Same discipline as
patch_docs_50/51 -- resolve and assert every anchor before writing anything.
"""
import sys
from pathlib import Path

ROOT = Path(r'D:\rblxTRGproject')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text, before):
    (ROOT / path).write_text(text, encoding='utf-8', newline='\n')
    print('%-26s %7d -> %7d chars' % (path, before, len(text)))


def append(path, block):
    text = read(path)
    before = len(text)
    if not text.endswith('\n'):
        text += '\n'
    write(path, text + block, before)


PROGRESS_APPEND = """
### 51.6 第二笔提交：git 主机不通，改走 `api.github.com`

Phase 51 的文档提交（本地 `f1aadb6`）**推不出去**：`git push` 连试五次，
分别报 `Empty reply from server` / `Recv failure: Connection was reset`，
最后三次稳定在 `Failed to connect to github.com port 443 after 21080 ms`。

但没有全断 —— 同一次测量里两个主机是分开的：

| 主机 | 结果 |
|---|---|
| `api.github.com` | **HTTP 200，0.43 s** |
| `github.com` | **000，21 s 超时** |

GitHub 的 git 传输和 REST API 是**两个域名**，在这台机器上前者被挡住、后者通。
所以改走 `/git/blobs` → `/git/trees` → `/git/commits` → `PATCH /git/refs/heads/main`
把**同一棵树**写上去，脚本是 `_tools/_attic/scratch/api_push.py`。

**这为什么不是「换了内容再推」：** git 的 tree sha 是**内容哈希**（对每条记录的
路径 + 模式 + blob sha 求哈希），所以脚本在动 ref 之前先断言
**服务器算出来的 tree sha == 本地 `HEAD^{tree}`**（`20c3caba…`）——
对上才证明远端那棵树和本地那次提交**逐字节相同**，而不是「看起来一样」。
再读回来核对：**192 条记录 = 176 个 blob + 16 个目录**，176 个 blob 逐个与
本地 `git ls-tree -r HEAD` 比对，**0 处不同**。

顺带：文件数 **175 → 176**（多的是 `patch_docs_51.py` 自己）。

**留下的一个坑（记下来，下次别当成事故）：** 远端那笔提交是 **`1109d362`**，
不是本地的 `f1aadb6` —— 内容一模一样（tree 相同、parent 相同、message 只差
GitHub 抹掉的一个结尾换行），但作者身份被换成了 GitHub 的
`andypeng1NB <132412750+andypeng1@users.noreply.github.com>`，而且**它那个对象里还有
复现不出来的头**：拿同样的 tree / parent / 作者 / 时间戳手工 `hash-object`，
出来的是 `dd3f8ba`，不是它。所以**下一笔 `git push` 会被判成 non-fast-forward**。
网络通的时候一行解决，**内容完全相同、不会丢东西**：

```
git fetch origin && git reset --hard origin/main
```
"""


DECISIONS_APPEND = """
143. WHEN ONE HOST OF A SERVICE IS BLOCKED, THE OTHER DOOR IS OPEN -- AND THE PROOF OF IDENTITY IS THE HASH, NOT THE TRANSFER.

    WHAT HAPPENED. The Phase 51 documentation commit could not be pushed. Five `git push` attempts
    failed, the last three stably at `Failed to connect to github.com port 443 after 21080 ms`. But
    `api.github.com` answered the same minute in 0.43 s. GitHub serves git transport and its REST API
    from different hostnames, and on this machine only one of them is reachable.

    WHY THAT IS NOT A WORKAROUND. Reaching the same content by a different door is a transport
    substitution, not a change to what got published. What makes it safe is that git's tree sha is a
    hash of the entries and their blob shas, so the server computes a value that must equal the local
    `HEAD^{tree}` if and only if the content is byte-identical. The script asserts that equality
    *before* it moves the ref, then reads the tree back and compares all 176 blobs against
    `git ls-tree -r HEAD`. The transfer is not the evidence; the hash is.

    THE PART TO REMEMBER. The resulting commit is NOT the local commit's sha. The author identity is
    replaced with the authenticated user's and a trailing newline is dropped -- and there is some
    header in GitHub's object that a reconstruction does not reproduce: same tree, same parent, same
    author, same timestamp, and the hand-built object still hashes to something else. So local and
    remote now hold content-identical commits with different hashes, and the next push will be
    refused as non-fast-forward. Write that down where it is created, with its one-line fix, rather
    than letting the next person meet it as an unexplained rejection. Content-identical is not the
    same claim as sha-identical, and only the second makes a push a no-op.

    HOW TO APPLY. When a service has separate hosts for its API and its data plane, measure them
    separately before concluding the service is down. Then, if you have to go in by the other door,
    pick an identity check the receiving side computes itself -- a content hash, not a byte count and
    not an echo of what you sent -- and fail before mutating anything if it does not match.
"""


CLAUDE_INS = """
**推送通道（同一天补的）：** `git push` 在这台机器上连不上 —— **`github.com:443` 21 s 超时**，
但**同分钟 `api.github.com` 200 / 0.43 s**；两个域名是分开的。于是用
`_tools/_attic/scratch/api_push.py` 走 Git Data API 把**同一棵树**写上去，动 ref 之前
**断言服务器算出的 tree sha == 本地 `HEAD^{tree}`**（tree sha 是内容哈希，对上就是逐字节相同），
写完再把 176 个 blob 读回来逐一比对，0 处不同。远端那笔是 **`1109d362`**、不是本地的
`f1aadb6`（内容相同，作者被换成 GitHub 身份），所以**下一次 `git push` 会是 non-fast-forward** ——
网络通时 `git fetch origin && git reset --hard origin/main` 一行解决，**不丢内容**。"""


def main():
    for p in ('PROGRESS.md', 'DECISIONS_2.md', 'CLAUDE.md'):
        read(p)

    prog = read('PROGRESS.md')
    if '51.6' in prog:
        sys.exit('PROGRESS.md already has a 51.6 -- not running twice')
    tail = '已进 `QUESTIONS.md` **P5**。'
    if not prog.rstrip().endswith(tail):
        sys.exit('PROGRESS.md: does not end with the Phase 51.5 tail -- '
                 'appending would put 51.6 in the wrong section')

    dec = read('DECISIONS_2.md')
    if dec.count('\n143. ') != 0:
        sys.exit('DECISIONS_2.md already has an entry 143')

    claude = read('CLAUDE.md')
    anchor = '逐字副本，现在公开了 —— 见 `QUESTIONS.md` **P5**。'
    if claude.count(anchor) != 1:
        sys.exit('CLAUDE.md: the Phase 51 anchor matched %d times'
                 % claude.count(anchor))
    i = claude.index(anchor) + len(anchor)

    write('CLAUDE.md', claude[:i] + CLAUDE_INS + claude[i:], len(claude))
    append('DECISIONS_2.md', DECISIONS_APPEND)
    append('PROGRESS.md', PROGRESS_APPEND)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
