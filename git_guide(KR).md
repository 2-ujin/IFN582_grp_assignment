# Git 사용 가이드 (KR)
<div align = "right">by Yujin Lee </div>

> 영어 원본: [git_guide.md](git_guide.md)

## 내 컴퓨터에 Git 설치하기
- 우리 GitHub 저장소: https://github.com/2-ujin/IFN582_grp_assignment

### Windows:
- git-scm.com/downloads 에서 Git for Windows를 다운로드합니다.
- 설치 프로그램을 실행하고 기본 옵션 그대로 진행합니다 ("Next"만 계속 클릭).
- 설치가 끝나면 시작 메뉴에서 "Git Bash"를 열어 제대로 설치됐는지 확인합니다.

### MAC:
- 터미널을 열고 다음을 입력합니다: git --version
- Git이 설치되어 있지 않으면 macOS가 "Command Line Developer Tools" 설치를 안내합니다 — Install을 클릭하세요.


## 저장소 Clone 하기

"Clone"은 프로젝트 전체(모든 변경 기록 포함)를 내 컴퓨터로 복사해 오는 것을 말합니다.

1. Git Bash(Windows) 또는 터미널(Mac)을 엽니다.
2. 프로젝트를 저장할 폴더로 이동합니다. 예:
```
 > cd Desktop
```
3. clone 명령어를 실행합니다:
```
 > git clone https://github.com/2-ujin/IFN582_grp_assignment.git
```
4. 모든 프로젝트 파일이 들어 있는 "IFN582_grp_assignment" 폴더가 생깁니다. 그 폴더로 이동합니다:
```
> cd IFN582_grp_assignment
```

## 저장소의 파일을 수정하고 올리는 방법

> **중요:** 메인 브랜치 `IFN582_grp_assignment`는 **보호(protected)** 되어 있습니다.
> 이 브랜치에는 `git push`를 **직접 할 수 없습니다** — 시도하면 다음 에러가 납니다:
> `GH013: Repository rule violations ... Changes must be made through a pull request.`
> 대신 **내 브랜치**에서 작업하고 **Pull Request(PR)** 를 열어서 팀원이 리뷰할 수 있게 해야 합니다.

### 전체 흐름
```
메인 브랜치 (IFN582_grp_assignment)
   │  1. git pull
   ├──► 2. 내 브랜치 만들기 (예: yujin-part1)
   │        3. 수정 → add → commit → push
   │        4. GitHub에서 Pull Request 열기
   │        5. 팀원 리뷰 → Merge
   ◄──────────┘
   6. 메인 브랜치로 돌아와서 git pull
```

### 1. 먼저 로컬 메인 브랜치를 최신 상태로 맞추기
```
> git switch IFN582_grp_assignment
> git pull
```

### 2. 내 브랜치 만들기
이름 + 작업 내용으로 정합니다. 예: `sky-home-page`, `queenie-auth`.
```
> git switch -c [브랜치 이름]
```
지금 어떤 브랜치에 있는지 확인하려면:
```
> git branch --show-current
```

### 3. 파일 수정 후 add → commit → push
add (스테이징 준비) > commit (라벨 붙이기) > push (GitHub에 업로드)
```
> git add [파일 이름]
> git commit -m "이번 commit에 대한 설명"
> git push -u origin [브랜치 이름]    # 새 브랜치를 처음 push할 때만
> git push                           # 그 다음부터는 이것만
```
- `git push`는 **commit된** 변경사항만 올립니다. `Everything up-to-date`가 뜨면 `git add` / `git commit`을 빠뜨렸을 가능성이 높습니다.
- `git status`로 아직 commit 안 된 파일을 확인할 수 있습니다.

### 4. Pull Request(PR) 열기
1. https://github.com/2-ujin/IFN582_grp_assignment 에 접속합니다.
2. **"Compare & pull request"** 를 클릭합니다 (또는 Pull requests → New pull request).
3. 확인: **base = `IFN582_grp_assignment`**, **compare = 내 브랜치**.
4. 짧은 제목과 변경 내용을 적고 **Create pull request** 를 클릭합니다.
5. 단톡방에 PR 링크를 올려서 누군가 리뷰할 수 있게 합니다.

### 5. 리뷰 & Merge
- **리뷰하는 사람:** PR 열기 → **Files changed** 탭 → 필요하면 코멘트 → **Review changes** → *Approve* (또는 *Request changes*).
- **PR 올린 사람:** 승인되면 **Merge pull request** 를 클릭합니다.
- merge 전에 고칠 게 있나요? **같은 브랜치**에서 commit하고 다시 `git push`만 하면 PR이 자동으로 업데이트됩니다. 새 PR을 열 필요가 없습니다.
- PR이 merge된 후에는 그 브랜치에 commit을 추가해도 PR에 반영되지 않습니다. 새 브랜치 + 새 PR로 시작하세요.

### 6. PR이 merge된 후
메인 브랜치로 돌아가서 최신 코드를 받은 다음, 다음 작업을 위해 **새 이름으로 새 브랜치를 만듭니다**:
```
> git switch IFN582_grp_assignment          # 1) 메인 브랜치로 돌아가기
> git pull                                  # 2) 최신 코드 받기 (merge된 내 PR 포함)
> git switch -c [새 브랜치 이름]             # 3) 새 브랜치 만들고 이동, 예: yujin-models
> git branch --show-current                 # 4) 새 브랜치에 있는지 확인
```

> **브랜치 1개 = PR 1개.**
> - PR이 아직 열려 있는 동안에는 **같은 브랜치**를 계속 사용하세요 — commit + push만 다시 하면 됩니다.
> - PR이 **merge된 후에는 그 브랜치를 다시 쓰지 마세요.** 팀원들의 최신 코드가 반영되지 않은 옛날 상태라서, 계속 작업하면 conflict가 나기 쉽습니다. 항상 최신 메인 브랜치에서 새 브랜치를 만드세요.

### 팁
- `IFN582_grp_assignment`에서 직접 commit하지 마세요 — commit 전에 항상 현재 브랜치를 확인하세요.
- 새 작업을 시작하기 전에 메인 브랜치에서 `git pull`을 해서 팀원들의 최신 코드를 받으세요.
- `project/__init__.py`에 있는 내 로컬 MySQL 비밀번호를 commit하지 마세요.
- PR에 **conflict**가 표시되면, 직접 해결하기 전에 단톡방에 먼저 물어보세요 — 보통 두 사람이 같은 줄을 수정했다는 뜻입니다.
