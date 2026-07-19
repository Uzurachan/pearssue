#!/usr/bin/env python3
"""Issue一覧を単体のHTMLファイルとしてエクスポートするスクリプト。

同僚などに「そのままファイルとして渡せる」共有物を作るためのもの。
list_issues.py と同じソート・フィルタに対応し、外部依存なしの
自己完結したHTMLファイルを1つ出力する。一覧のid列はリンクになっており、
押すとページ内の詳細(アコーディオン)が開く。
"""

import argparse
import datetime
import html

from aissue_common import collect_issues, issue_sort_key, list_attachments, load_config

VALID_STATUSES = {"new", "processing", "pending", "done"}
VALID_PRIORITIES = {"high", "medium", "low"}

DEFAULT_OUTPUT = "issues.html"

META_FIELDS = ["status", "priority", "tags", "assignee", "order", "created", "updated"]

PAGE_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Issue一覧</title>
<style>
{style}
</style>
</head>
<body id="top">
<h1>Issue一覧</h1>
<p class="generated">生成日時: {generated_at}</p>
{table}
<h2>詳細</h2>
{details}
<a href="#top" class="back-to-top" aria-label="一番上へ戻る">&uarr; Top</a>
<script>
{script}
</script>
</body>
</html>
"""

STYLE = """
html { scroll-behavior: smooth; }
body { font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif; margin: 2rem; color: #1a1a1a; background: #fff; }
h1 { font-size: 1.4rem; }
h2 { font-size: 1.1rem; margin-top: 2rem; }
.generated { color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; font-size: 0.9rem; }
th { background: #f5f5f5; }
tr:nth-child(even) { background: #fafafa; }
a { color: #1d4ed8; text-decoration: none; }
a:hover { text-decoration: underline; }
.status { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.8rem; white-space: nowrap; }
.status-new { background: #e0e7ff; color: #3730a3; }
.status-processing { background: #fef3c7; color: #92400e; }
.status-pending { background: #fee2e2; color: #991b1b; }
.status-done { background: #dcfce7; color: #166534; }
.status-other { background: #eee; color: #333; }
.priority-high { font-weight: bold; color: #b91c1c; }
.priority-medium { color: #333; }
.priority-low { color: #666; }
.priority-other { color: #333; }
.issue-detail { border: 1px solid #ddd; border-radius: 6px; margin-bottom: 0.75rem; padding: 0.25rem 0.75rem; }
.issue-detail summary { cursor: pointer; font-weight: bold; padding: 0.5rem 0; }
.issue-detail table.meta-table { margin: 0.5rem 0 1rem; width: auto; }
.issue-detail table.meta-table th { width: 6rem; }
.issue-detail .body { white-space: pre-wrap; line-height: 1.6; margin-bottom: 1rem; }
.issue-detail .attachments ul { margin: 0.25rem 0 1rem; padding-left: 1.5rem; }
.back-to-top {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  background: #1d4ed8;
  color: #fff;
  padding: 0.6rem 1rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.back-to-top:hover { background: #1e40af; text-decoration: none; }
"""

SCRIPT = """
function openTargetDetail() {
  var id = location.hash.slice(1);
  if (!id) return;
  var el = document.getElementById(id);
  if (el && el.tagName === 'DETAILS') {
    el.open = true;
    el.scrollIntoView();
  }
}
window.addEventListener('hashchange', openTargetDetail);
window.addEventListener('DOMContentLoaded', openTargetDetail);
"""

HEADERS = ["order", "id", "status", "priority", "title", "tags", "assignee"]


def css_key(value, valid_values):
    return value if value in valid_values else "other"


def detail_anchor(issue_id):
    return f"issue-detail-{issue_id}"


def build_table(issues):
    header_html = "".join(f"<th>{h}</th>" for h in HEADERS)
    rows_html = []
    for issue in issues:
        order = issue.get("order")
        order_display = str(order) if isinstance(order, int) else "-"
        issue_id = str(issue.get("id", ""))
        status = str(issue.get("status", ""))
        priority = str(issue.get("priority", ""))
        tags = issue.get("tags") or []
        tags_display = ", ".join(str(t) for t in tags)

        cells = [
            html.escape(order_display),
            f'<a href="#{detail_anchor(issue_id)}">{html.escape(issue_id)}</a>',
            f'<span class="status status-{css_key(status, VALID_STATUSES)}">{html.escape(status)}</span>',
            f'<span class="priority-{css_key(priority, VALID_PRIORITIES)}">{html.escape(priority)}</span>',
            html.escape(str(issue.get("title", ""))),
            html.escape(tags_display),
            html.escape(str(issue.get("assignee", ""))),
        ]
        rows_html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")

    return (
        "<table>\n<thead><tr>" + header_html + "</tr></thead>\n<tbody>\n"
        + "\n".join(rows_html)
        + "\n</tbody>\n</table>"
    )


def build_meta_table(issue):
    rows = []
    for field in META_FIELDS:
        value = issue.get(field)
        if field == "tags":
            display = ", ".join(str(t) for t in (value or []))
        elif field == "order":
            display = str(value) if isinstance(value, int) else "-"
        else:
            display = str(value) if value is not None else ""
        rows.append(f"<tr><th>{html.escape(field)}</th><td>{html.escape(display)}</td></tr>")
    return '<table class="meta-table">\n' + "\n".join(rows) + "\n</table>"


def build_attachments_html(issues_dir, issue_id, attachments_dir_name):
    files = list_attachments(issues_dir, issue_id, attachments_dir_name)
    if not files:
        return ""
    items = "\n".join(f"<li><code>{html.escape(name)}</code></li>" for name in files)
    return f'<div class="attachments"><strong>添付ファイル</strong><ul>\n{items}\n</ul></div>'


def build_details(issues, issues_dir, attachments_dir_name):
    sections = []
    for issue in issues:
        issue_id = str(issue.get("id", ""))
        title = str(issue.get("title", ""))
        body = issue.get("body", "")
        attachments_html = build_attachments_html(issues_dir, issue_id, attachments_dir_name)

        sections.append(
            f'<details id="{detail_anchor(issue_id)}" class="issue-detail">\n'
            f"<summary>{html.escape(issue_id)}: {html.escape(title)}</summary>\n"
            f"{build_meta_table(issue)}\n"
            f'<div class="body">{html.escape(body)}</div>\n'
            f"{attachments_html}\n"
            f"</details>"
        )
    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Issue一覧をHTMLファイルとして出力する")
    parser.add_argument(
        "--sort", choices=["order", "priority", "created", "id"], default="order",
        help="並べ替えキー(デフォルト: order)",
    )
    parser.add_argument("--status", help="指定したstatusのIssueのみ出力する")
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"出力先ファイルパス(デフォルト: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    config = load_config()
    issues_dir = config["issues_dir"]
    issues = collect_issues(issues_dir)

    if args.status:
        issues = [i for i in issues if i.get("status") == args.status]

    issues.sort(key=issue_sort_key(args.sort))

    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if issues:
        table = build_table(issues)
        details = build_details(issues, issues_dir, config["attachments_dir"])
    else:
        table = "<p>Issueが見つかりません。</p>"
        details = ""

    page = PAGE_TEMPLATE.format(
        style=STYLE,
        generated_at=html.escape(generated_at),
        table=table,
        details=details,
        script=SCRIPT,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(page)

    print(args.output)


if __name__ == "__main__":
    main()
