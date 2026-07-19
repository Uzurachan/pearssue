<p align="center">
  <img src="./assets/logo.svg" alt="Pearssue logo" width="160">
</p>

# Pearssue（AIと一緒に育てるタスク帳）

人間にもAIエージェントにも読めるMarkdownベースのIssue管理ツール。DBもサーバーも不要で、Gitでそのまま差分管理できる。

## 特徴

- **人間もAIもそのまま読める**: 1 Issue = 1ディレクトリの`index.md`(Markdown + YAML frontmatter)。特別なビューアなしでエディタやGitHub上でそのまま読める
- **Claude Codeなら自然言語で操作できる**: 「Issue作って」「一覧見せて」「これ完了にして」と話しかけるだけで、対応するSkillが自動で発火する
- **複数プロジェクトを横断管理できる**: ツール本体(このリポジトリ)とタスクデータを分離できるので、1箇所のタスク管理データを複数プロジェクトの作業から参照できる
- **ファイルで共有できる**: 一覧を外部依存なしの単体HTMLファイルとして出力し、メールやチャットでそのまま渡せる

## クイックスタート

```sh
git clone <このリポジトリのURL> pearssue
cd pearssue
python3 init.py
```

`init.py`が対話式でIssue IDの形式などを聞いてくるので、基本はEnterキーでデフォルト値のまま進めればよい(詳しくは[セットアップ](#セットアップ)を参照)。

セットアップが終わったら、最初のIssueを作ってみる:

```sh
echo "## 概要
最初のテストIssue" | python3 new_issue.py --title "動作確認用のIssue"
python3 list_issues.py
```

Claude Codeを使っている場合は、コマンドを覚える必要はない。「Issue作って」「一覧見せて」のように話しかけるだけでよい(各セクションで詳しく説明する)。

## Issueの構造

1つのIssueは1つのディレクトリで、直下に`index.md`(必須)と`attachments/`(任意、添付ファイル用)を持つ。

```
issues/
  0001/
    index.md          # frontmatter + 本文
    attachments/       # ログ・スクリーンショット・設計メモなど(任意)
```

`index.md`の冒頭にはYAML frontmatterでメタデータを記載する:

| フィールド | 内容 | 例 |
|---|---|---|
| `id` | Issue ID | `"0001"` |
| `title` | タイトル | `"ログインボタンが反応しない"` |
| `status` | 状態(下記参照) | `new` |
| `priority` | 優先度 | `high` / `medium` / `low` |
| `tags` | タグ(複数可) | `[bug, frontend]` |
| `assignee` | 担当者 | `unassigned` |
| `order` | やる順番(数値、小さいほど先。未設定は`null`) | `1` |
| `created` / `updated` | 作成日 / 更新日 | `2026-07-19` |

実際のサンプルは[`examples/issues/`](examples/issues/)を参照。

## 使い方

### Issueを作る

Claude Codeを使っている場合は、「バグ報告したい」「Issue作って」のように話しかけるだけでよい。
`.claude/skills/create-issue/SKILL.md` が発火し、対話でヒアリングした内容から自動でIssueを作成する。

手動で作成する場合は `new_issue.py` を直接叩く:

```sh
echo "## 概要
ここに本文を書く。" | python3 new_issue.py \
  --title "Issueのタイトル" \
  --status new \
  --priority medium \
  --tags "bug,frontend" \
  --assignee unassigned
```

`.pearssue.json` の `id_format` に従って次のIDが自動採番され、`<issues_dir>/<id>/index.md` が生成される。

### ステータスを更新する

ステータス値は `new`(未着手) / `processing`(対応中) / `pending`(保留) / `done`(完了)の4つ。状態遷移に制限はなく、どこからどこへでも変更できる。

Claude Codeを使っている場合は、「Issue 0001をdoneにして」のように話しかけるだけでよい。
`.claude/skills/update-issue-status/SKILL.md` が発火し、対象Issueを特定して更新する。

手動で更新する場合は `update_status.py` を直接叩く:

```sh
python3 update_status.py --id 0001 --status pending --note "レビュー担当者からの返答待ち"
```

`--note` は任意。指定すると変更理由が本文末尾に追記される。

### 一覧を見る・並べ替える

Claude Codeを使っている場合は、「Issue一覧見せて」「Aを先にやって」のように話しかけるだけでよい。
`.claude/skills/list-issues/SKILL.md` が発火し、表示や並べ替えを行う。

手動で一覧表示する場合:

```sh
python3 list_issues.py                # order昇順で表示(デフォルト)
python3 list_issues.py --sort priority
python3 list_issues.py --status processing
```

手動で並べ替える場合:

```sh
# 0003, 0001, 0002 の順にorder=1,2,3を設定する
python3 reorder_issues.py --sequence 0003,0001,0002

# 1件だけorderを調整する
python3 reorder_issues.py --id 0001 --order 1
```

### 詳細を見る

Claude Codeを使っている場合は、「Issue 0001の詳細見せて」「一番上のissue見せて」のように話しかけるだけでよい。
`.claude/skills/show-issue/SKILL.md` が発火し、決まったフォーマット(メタデータテーブル→本文→添付ファイル一覧)で表示する。読み取り専用のため専用スクリプトはなく、`index.md`をそのまま読んで表示する。

### 同僚と共有する(HTML出力)

一覧を同僚などにファイルとしてそのまま渡したい場合は、外部依存のない単体HTMLファイルを出力できる。

Claude Codeを使っている場合は、「同僚に共有できる形にして」「HTMLで書き出して」のように話しかけるだけでよい。
`.claude/skills/list-issues/SKILL.md` が発火し、`export_html.py` を実行する。

手動で出力する場合:

```sh
python3 export_html.py --output issues.html
python3 export_html.py --status processing --output processing.html
```

`list_issues.py` と同じ `--sort` / `--status` オプションが使える。生成された `issues.html` はブラウザで開けるほか、メールやチャットでそのまま送って共有できる。

一覧テーブルの各id(例: `0001`)はページ内リンクになっており、押すとそのIssueの詳細(メタデータ・本文・添付ファイル一覧)が同じファイル内でアコーディオン展開される。ファイルは1つのままなので、送るのも開くのも`issues.html`単体で完結する。

## セットアップ

初回セットアップは対話式スクリプトで行う。Issue IDの形式やデータの保存先を決めて `.pearssue.json` に保存する。

```sh
python3 init.py
```

対話で決められること:

- Issue IDの形式(連番 / 日付+連番 / ULID)
- Issueを格納するディレクトリのパス(デフォルト: `../pearssue-data/issues`。このリポジトリの外を推奨)
- 添付ファイル用のサブディレクトリ名(デフォルト: `attachments`)

`.pearssue.json`はリポジトリ内に作られるが`.gitignore`で除外されており、各自がcloneしたら
最初に`init.py`を実行して自分のデータ保存先を設定する。リポジトリ内のパスを指定した場合は
誤コミットのリスクについて警告が出る。

実行すると設定ファイル `.pearssue.json` と、Issue格納用ディレクトリが作成される。

## 複数プロジェクトを横断してタスク管理する

このリポジトリは「ツール一式」として1箇所にcloneし、実際のタスクデータ(`issues/`)は
このリポジトリの外(兄弟ディレクトリなど)に置く運用を想定している。

```
~/dev/pearssue/         <- このリポジトリ(clone)
~/dev/pearssue-data/    <- タスクデータ(init.pyで作成、Git管理外)
```

こうしておくと、複数の別プロジェクトで作業していても常に同じ`pearssue-data`を参照でき、
かつタスクデータをどこかのプロジェクトリポジトリに誤ってコミットする事故を防げる。

## もっと詳しく

設計方針やIssueスキーマの詳細は[`AGENTS.md`](AGENTS.md)を参照。
