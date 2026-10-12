# How to use git?
<div align = "right">by Yujin Lee </div>

## Install Git on Your Computer
- our github repository: https://github.com/2-ujin/IFN582_grp_assignment

### Windows:
- Go to git-scm.com/downloads and download Git for Windows.
- Run the installer and keep all default options (just click “Next” through the setup).
- After installation, open “Git Bash” from the Start menu to confirm it installed correctly.

### MAC:
- Open Terminal and type: git --version
- If Git is not installed, macOS will prompt you to install the “Command Line Developer Tools” — click Install.


## Clone the Repository

"Cloning” means downloading a full copy of the project (with its full history) onto your computer.

1. Open Git Bash (Windows) or Terminal (Mac).
2. Navigate to the folder where you want to save the project, for example:
```
 > cd Desktop
```
3. Run the clone command:
```
 > git clone https://github.com/2-ujin/IFN582_grp_assignment.git
```
4. This creates a new folder called "IFN582_grp_assignment" containing all the project files. Move into it:
```
> cd IFN582_grp_assignment
```
(I just ask claude to clone the github repository and my local computer, if u guys have clone or other AI tool they might explain better than me )

## How to update & Modify file in the repository?

> **Important:** The main branch `IFN582_grp_assignment` is **protected**.
> You **cannot** `git push` to it directly — if you try, you will get
> `GH013: Repository rule violations ... Changes must be made through a pull request.`
> Instead, work on **your own branch** and open a **Pull Request (PR)** so the team can review it.

### Overview
```
main branch (IFN582_grp_assignment)
   │  1. git pull
   ├──► 2. create your branch (e.g. yujin-part1)
   │        3. modify → add → commit → push
   │        4. open a Pull Request on GitHub
   │        5. teammate reviews → Merge
   ◄──────────┘
   6. switch back to main branch and git pull
```

### 1. Sync your local main branch first
```
> git switch IFN582_grp_assignment
> git pull
```

### 2. Create your own branch
Use your name + what you are working on, e.g. `sky-home-page`, `queenie-auth`.
(I simply named my branch as `yujin-part1` lol)

```
> git switch -c [your-branch-name]
```
Check which branch you are on at any time:
```
> git branch --show-current
```

### 3. Modify files, then add → commit → push
add (ready for staging) > commit (labelling) > push (upload to GitHub)
```
> git add [file name]
> git commit -m "the description of this commit"
> git push -u origin [your-branch-name]    # first push of a new branch only
> git push                                 # after that, just this
```
- `git push` only uploads **committed** changes. If you see `Everything up-to-date`, you probably forgot `git add` / `git commit`.
- `git status` shows what is not committed yet.

### 4. Open a Pull Request (PR)
1. Go to https://github.com/2-ujin/IFN582_grp_assignment
2. Click **"Compare & pull request"** (or Pull requests → New pull request).
3. Check: **base = `IFN582_grp_assignment`**, **compare = your branch**.
4. Write a short title + what you changed, then **Create pull request**.
5. Post the PR link in our group chat so someone can review it.

### 5. Review & Merge
- **Reviewer:** open the PR → **Files changed** tab → leave comments if needed → **Review changes** → *Approve* (or *Request changes*).
- **Author:** once approved, click **Merge pull request**.
- Need to fix something before merging? Just commit and `git push` again on the **same branch** — the PR updates automatically. No need to open a new PR.
- After a PR is merged, new commits on that branch are NOT added to it. Start a new branch + new PR instead.

### 6. After your PR is merged
Switch back to the main branch, get the latest code, then **create a new branch with a new name** for your next task:
```
> git switch IFN582_grp_assignment          # 1) go back to the main branch
> git pull                                  # 2) get the latest code (incl. your merged PR)
> git switch -c [new-branch-name]           # 3) create + move to a new branch, e.g. yujin-models
> git branch --show-current                 # 4) check you are on the new branch
```

> **One branch = one PR.**
> - While your PR is still open, keep using the **same branch** — just commit + push again.
> - Once the PR is **merged**, **don't reuse that branch**. It is now out of date with teammates' code, so continuing on it easily causes conflicts. Always start a new branch from the latest main branch.

### Tips
- Never commit on `IFN582_grp_assignment` directly — always check your branch before committing.
- Before starting new work, `git pull` on the main branch so you have the latest version of teammates' code.
- Don't commit your local MySQL password in `project/__init__.py`.
- If a PR shows a **conflict**, ask in the group chat before resolving it — it usually means two people edited the same lines.
