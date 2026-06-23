# Git history — reconstitute and push

The full version history of this planning round (6 logical commits on branch `main`) is delivered as a single verified file at the repo root:

```
tagalog_tutor_history.bundle
```

**Why a bundle and not a live `.git` folder?** This project folder is mounted into the assistant's sandbox in a way that blocks the file-locking/delete operations Git needs, so a live `.git` could not be created here reliably. A bundle is Git's official single-file transport for exactly this situation. It is byte-verifiable (`git bundle verify`) and contains the complete history. On your own Windows machine, Git works normally.

The working files you already see in this folder are identical to the final commit's contents.

---

## Fastest path — clone the history into a sibling folder, then push

Open a terminal (PowerShell or Git Bash) and run:

```bash
cd C:\Users\tschu\Codex\Projects
git clone Tagalog-Claude\tagalog_tutor_history.bundle Tagalog-Claude-repo
cd Tagalog-Claude-repo
git log --oneline        # confirm 6 commits, branch main
```

`Tagalog-Claude-repo` is now a normal Git repository with full history and every file checked out. To publish it, create an EMPTY repo on your host (GitHub/GitLab/etc.), then:

```bash
git remote add origin https://github.com/<you>/<your-repo>.git
git push -u origin main
```

That's the push. Nothing here was faked — there is no remote configured yet because none was available during the session.

After pushing, record the remote URL + branch in `tagalog_tutor_project_starter/PROJECT_STATE.md` (Git status section).

---

## Optional — make THIS folder the repository instead

If you want `C:\Users\tschu\Codex\Projects\Tagalog-Claude` itself to be the repo (rather than the sibling clone):

```bash
cd C:\Users\tschu\Codex\Projects\Tagalog-Claude
git init -b main
git fetch tagalog_tutor_history.bundle main:main-history
git reset --soft main-history     # adopt history; your working files are untouched
git branch -d main-history
git status                        # should be clean (files already match the final commit)
```

Then add a remote and `git push -u origin main` as above.

(If `git status` shows differences, it only means a file was touched after the bundle was made; `git add -A && git commit` to capture it.)

---

## Verify the bundle first (optional, recommended)

```bash
git bundle verify Tagalog-Claude\tagalog_tutor_history.bundle
```

Expected: it reports the bundle is OK and lists `main` as a ref it requires no prerequisites for.

## Commit history in the bundle

```
docs: add independent proposal + project-state and push handoff
test: add end-to-end review workflow fixtures (magpatingin PoC)
feat: scaffold transparent FSRS-lite scheduler prototype
docs: define learner model, scheduling, evaluation, and tutoring architecture
docs: add research findings (learning science, current apps, Tagalog pedagogy, synthesis, sources)
chore: import and preserve source materials
```
