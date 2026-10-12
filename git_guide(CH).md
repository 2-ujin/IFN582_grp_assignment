# Git 使用指南 (CH)
<div align = "right">by Yujin Lee </div>

> 英文原版：[git_guide.md](git_guide.md)

## 在電腦上安裝 Git
- 我們的 GitHub 儲存庫：https://github.com/2-ujin/IFN582_grp_assignment

### Windows：
- 前往 git-scm.com/downloads 下載 Git for Windows。
- 執行安裝程式，全部保留預設選項（一直按「Next」即可）。
- 安裝完成後，從開始選單開啟「Git Bash」，確認是否安裝成功。

### MAC：
- 開啟終端機（Terminal），輸入：git --version
- 如果尚未安裝 Git，macOS 會提示你安裝「Command Line Developer Tools」— 點選 Install。


## Clone 儲存庫

「Clone」是指把整個專案（包含所有修改紀錄）完整下載一份到你的電腦。

1. 開啟 Git Bash（Windows）或終端機（Mac）。
2. 移動到你想存放專案的資料夾，例如：
```
 > cd Desktop
```
3. 執行 clone 指令：
```
 > git clone https://github.com/2-ujin/IFN582_grp_assignment.git
```
4. 會產生一個名為「IFN582_grp_assignment」的資料夾，裡面有所有專案檔案。進入該資料夾：
```
> cd IFN582_grp_assignment
```

## 如何修改並上傳儲存庫中的檔案？

> **重要：** 主分支 `IFN582_grp_assignment` 已被設為**受保護（protected）**。
> 你**不能**直接對它 `git push` — 如果嘗試，會出現以下錯誤：
> `GH013: Repository rule violations ... Changes must be made through a pull request.`
> 請改在**自己的分支**上工作，並開一個 **Pull Request（PR）**，讓組員可以審查（review）。

### 整體流程
```
主分支 (IFN582_grp_assignment)
   │  1. git pull
   ├──► 2. 建立自己的分支（例如 yujin-part1）
   │        3. 修改 → add → commit → push
   │        4. 在 GitHub 上開 Pull Request
   │        5. 組員審查 → Merge
   ◄──────────┘
   6. 切回主分支並 git pull
```

### 1. 先同步本機的主分支
```
> git switch IFN582_grp_assignment
> git pull
```

### 2. 建立自己的分支
用「名字 + 工作內容」命名，例如：`sky-home-page`、`queenie-auth`。
```
> git switch -c [分支名稱]
```
隨時查看目前所在的分支：
```
> git branch --show-current
```

### 3. 修改檔案，然後 add → commit → push
add（準備暫存）> commit（加上標記）> push（上傳到 GitHub）
```
> git add [檔案名稱]
> git commit -m "這次 commit 的說明"
> git push -u origin [分支名稱]    # 只有新分支第一次 push 時需要
> git push                        # 之後只要這樣即可
```
- `git push` 只會上傳**已 commit** 的修改。如果看到 `Everything up-to-date`，很可能是忘了 `git add` / `git commit`。
- 用 `git status` 可以查看哪些檔案還沒 commit。

### 3-1. 工作途中主分支有更新？同步你的分支
如果你還在工作時，組員的 PR 已經 merge，你的分支就會落後於主分支。
（PR 頁面會顯示 *"This branch is out-of-date with the base branch"*。）
請把最新的主分支合併到**你的**分支：
```
> git branch --show-current                         # 1) 確認你在自己的分支上
> git add [檔案名稱]                                 # 2) 先 commit 目前的工作
> git commit -m "WIP: 工作說明"
> git fetch origin                                  # 3) 下載最新的主分支
> git merge origin/IFN582_grp_assignment --no-edit  # 4) 把最新主分支合併到你的分支
> git push                                          # 5) 上傳 — PR 會自動更新
```
- **沒有衝突：** 完成。你的分支現在包含組員最新的程式碼 + 你的工作。
- **有衝突**（`CONFLICT (content): Merge conflict in ...`）：
  1. 在 VS Code 開啟該檔案，選擇 *Accept Current*（你的）/ *Accept Incoming*（主分支）/ *Accept Both*。
  2. 存檔後：
  ```
  > git add [檔案名稱]
  > git commit --no-edit
  > git push
  ```
  3. 不確定要保留哪段程式碼？請在群組聊天室詢問寫那段程式碼的組員。
- 想中途取消 merge：`git merge --abort`（回到步驟 4 之前的狀態）。
- 要幫**組員的分支**修改？步驟相同，但先執行 `git fetch origin` → `git switch [組員分支]` → `git pull`。並提醒組員繼續工作前先 `git pull`。

### 4. 開 Pull Request（PR）
1. 前往 https://github.com/2-ujin/IFN582_grp_assignment
2. 點選 **「Compare & pull request」**（或 Pull requests → New pull request）。
3. 確認：**base = `IFN582_grp_assignment`**，**compare = 你的分支**。
4. 寫一個簡短標題和修改內容，然後點 **Create pull request**。
5. 把 PR 連結貼到群組聊天室，讓其他人可以審查。

### 5. 審查與 Merge
- **審查者：** 開啟 PR → **Files changed** 分頁 → 需要時留下評論 → **Review changes** → *Approve*（或 *Request changes*）。
- **PR 發起者：** 通過審查後，點 **Merge pull request**。
- Merge 前還需要修改？只要在**同一個分支**上 commit 並再次 `git push`，PR 就會自動更新，不需要開新的 PR。
- PR merge 之後，再對該分支新增的 commit 不會加入那個 PR。請建立新分支 + 新 PR。

### 6. PR merge 之後
切回主分支、取得最新程式碼，然後為下一個工作**用新的名稱建立新分支**：
```
> git switch IFN582_grp_assignment          # 1) 切回主分支
> git pull                                  # 2) 取得最新程式碼（包含已 merge 的 PR）
> git switch -c [新分支名稱]                 # 3) 建立並切換到新分支，例如 yujin-models
> git branch --show-current                 # 4) 確認目前在新分支上
```

> **一個分支 = 一個 PR。**
> - PR 還沒 merge 時，請繼續使用**同一個分支** — 只要再次 commit + push 即可。
> - PR **merge 之後，請不要再使用那個分支。** 它已經沒有組員最新的程式碼，繼續在上面工作很容易產生衝突。請一律從最新的主分支建立新分支。

### 小提醒
- 不要直接在 `IFN582_grp_assignment` 上 commit — commit 前一定要確認目前所在的分支。
- 開始新工作前，先在主分支 `git pull`，取得組員最新的程式碼。
- 不要把 `project/__init__.py` 裡你本機的 MySQL 密碼 commit 上去。
- 如果 PR 顯示 **conflict（衝突）**，請先在群組聊天室詢問再處理 — 通常代表兩個人修改了同一行。
