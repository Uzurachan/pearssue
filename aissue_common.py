"""aissueの各スクリプトで共有する設定読み込み・frontmatter操作ユーティリティ。"""

import json
import os
import re

CONFIG_PATH = ".aissue.json"

DEFAULT_CONFIG = {
    "id_format": "sequential",
    "issues_dir": "issues",
    "attachments_dir": "attachments",
}

FRONTMATTER_DELIMITER = "---"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return {**DEFAULT_CONFIG, **config}


def yaml_str(value):
    """PythonのstrをYAML(frontmatter)上で安全なクォート付き文字列にする。"""
    return json.dumps(value, ensure_ascii=False)


def split_frontmatter(text):
    """index.mdのテキストを (frontmatter文字列, 残りの本文) に分割する。"""
    prefix = f"{FRONTMATTER_DELIMITER}\n"
    if not text.startswith(prefix):
        raise ValueError("index.md にfrontmatterが見つかりません")
    end = text.index(f"\n{FRONTMATTER_DELIMITER}", len(prefix))
    frontmatter = text[len(prefix):end]
    rest = text[end + len(f"\n{FRONTMATTER_DELIMITER}"):]
    return frontmatter, rest


def replace_field(frontmatter, field, raw_value):
    """frontmatter文字列内の `field: ...` 行を書き換える(なければ末尾に追加する)。"""
    pattern = re.compile(rf"^{field}:.*$", re.MULTILINE)
    line = f"{field}: {raw_value}"
    if pattern.search(frontmatter):
        return pattern.sub(line, frontmatter, count=1)
    return frontmatter + f"\n{line}"


def _yaml_unquote(value):
    value = value.strip()
    if value == "[]":
        return []
    if value == "null" or value == "":
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        return value


def parse_frontmatter(frontmatter):
    """frontmatter文字列(区切り線を除いた中身)を簡易的にdictへパースする。

    独自のIssueスキーマ(トップレベルのkey: valueと、配列の`- item`)だけを
    扱えれば十分なため、汎用YAMLパーサーは実装しない。
    """
    data = {}
    lines = frontmatter.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            items = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("- "):
                items.append(_yaml_unquote(lines[j].strip()[2:]))
                j += 1
            data[key] = items
            i = j
            continue
        data[key] = _yaml_unquote(value)
        i += 1
    return data


def read_issue_text(index_path):
    """index.mdを読み、(frontmatter dict, 本文str) のタプルを返す。"""
    with open(index_path, "r", encoding="utf-8") as f:
        text = f.read()
    frontmatter, body = split_frontmatter(text)
    return parse_frontmatter(frontmatter), body.strip()


def read_issue(index_path):
    """index.mdを読み、frontmatterをdictとして返す。"""
    data, _ = read_issue_text(index_path)
    return data


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def collect_issues(issues_dir):
    """issues_dir配下の全Issueのfrontmatterをdictのリストとして返す(id順)。

    各dictには本文が `body` キーで(frontmatterを除いた文字列として)含まれる。
    """
    issues = []
    if not os.path.isdir(issues_dir):
        return issues
    for name in sorted(os.listdir(issues_dir)):
        index_path = os.path.join(issues_dir, name, "index.md")
        if not os.path.isfile(index_path):
            continue
        data, body = read_issue_text(index_path)
        data.setdefault("id", name)
        data["body"] = body
        issues.append(data)
    return issues


def list_attachments(issues_dir, issue_id, attachments_dir_name):
    """Issueの添付ファイル名一覧(ファイル名のみ)を返す。"""
    attach_dir = os.path.join(issues_dir, issue_id, attachments_dir_name)
    if not os.path.isdir(attach_dir):
        return []
    return sorted(
        name
        for name in os.listdir(attach_dir)
        if os.path.isfile(os.path.join(attach_dir, name))
    )


def issue_sort_key(sort_by):
    """`issues.sort(key=issue_sort_key(sort_by))` として使うキー関数を返す。"""

    def key(issue):
        if sort_by == "order":
            order = issue.get("order")
            return (0, order) if isinstance(order, int) else (1, str(issue.get("id", "")))
        if sort_by == "priority":
            return PRIORITY_ORDER.get(issue.get("priority"), 99)
        if sort_by == "created":
            return issue.get("created") or ""
        return str(issue.get("id", ""))

    return key
