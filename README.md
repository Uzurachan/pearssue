# aissue
AI Issue template

## セットアップ

初回セットアップは対話式スクリプトで行う。Issue IDの形式やディレクトリ名を決めて `.aissue.json` に保存する。

```sh
python3 init.py
```

対話で決められること:

- Issue IDの形式(連番 / 日付+連番 / ULID)
- Issueを格納するディレクトリ名(デフォルト: `issues`)
- 添付ファイル用のサブディレクトリ名(デフォルト: `attachments`)

実行すると設定ファイル `.aissue.json` と、Issue格納用ディレクトリが作成される。
Issueディレクトリの構成例は `examples/issues/` を参照。

## Issueの作成

**Claude Codeを使っている場合**は、「バグ報告したい」「Issue作って」のように話しかけるだけでよい。
`.claude/skills/create-issue/SKILL.md` が発火し、対話でヒアリングした内容から自動でIssueを作成する。

**手動で作成する場合**は `new_issue.py` を直接叩く:

```sh
echo "## 概要
ここに本文を書く。" | python3 new_issue.py \
  --title "Issueのタイトル" \
  --status new \
  --priority medium \
  --tags "bug,frontend" \
  --assignee unassigned
```

`.aissue.json` の `id_format` に従って次のIDが自動採番され、`<issues_dir>/<id>/index.md` が生成される。

## ステータスの更新

ステータス値は `new`(未着手) / `processing`(対応中) / `pending`(保留) / `done`(完了)の4つ。状態遷移に制限はなく、どこからどこへでも変更できる。

**Claude Codeを使っている場合**は、「Issue 0001をdoneにして」のように話しかけるだけでよい。
`.claude/skills/update-issue-status/SKILL.md` が発火し、対象Issueを特定して更新する。

**手動で更新する場合**は `update_status.py` を直接叩く:

```sh
python3 update_status.py --id 0001 --status pending --note "レビュー担当者からの返答待ち"
```

`--note` は任意。指定すると変更理由が本文末尾に追記される。

## 一覧表示・並べ替え

各Issueは `order`(やる順番、数値。小さいほど先)というフィールドを持つ。未設定は `null` で、一覧では末尾に `-` 表示される。

**Claude Codeを使っている場合**は、「Issue一覧見せて」「Aを先にやって」のように話しかけるだけでよい。
`.claude/skills/list-issues/SKILL.md` が発火し、表示や並べ替えを行う。

**手動で一覧表示する場合**:

```sh
python3 list_issues.py                # order昇順で表示(デフォルト)
python3 list_issues.py --sort priority
python3 list_issues.py --status processing
```

**手動で並べ替える場合**:

```sh
# 0003, 0001, 0002 の順にorder=1,2,3を設定する
python3 reorder_issues.py --sequence 0003,0001,0002

# 1件だけorderを調整する
python3 reorder_issues.py --id 0001 --order 1
```

## Issueの詳細表示

**Claude Codeを使っている場合**は、「Issue 0001の詳細見せて」「一番上のissue見せて」のように話しかけるだけでよい。
`.claude/skills/show-issue/SKILL.md` が発火し、決まったフォーマット(メタデータテーブル→本文→添付ファイル一覧)で表示する。読み取り専用のため専用スクリプトはなく、`index.md`をそのまま読んで表示する。

## 同僚への共有(HTML出力)

一覧を同僚などにファイルとしてそのまま渡したい場合は、外部依存のない単体HTMLファイルを出力できる。

**Claude Codeを使っている場合**は、「同僚に共有できる形にして」「HTMLで書き出して」のように話しかけるだけでよい。
`.claude/skills/list-issues/SKILL.md` が発火し、`export_html.py` を実行する。

**手動で出力する場合**:

```sh
python3 export_html.py --output issues.html
python3 export_html.py --status processing --output processing.html
```

`list_issues.py` と同じ `--sort` / `--status` オプションが使える。生成された `issues.html` はブラウザで開けるほか、メールやチャットでそのまま送って共有できる。

一覧テーブルの各id(例: `0001`)はページ内リンクになっており、押すとそのIssueの詳細(メタデータ・本文・添付ファイル一覧)が同じファイル内でアコーディオン展開される。ファイルは1つのままなので、送るのも開くのも`issues.html`単体で完結する。
