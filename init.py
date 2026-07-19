#!/usr/bin/env python3
"""aissue の初回セットアップスクリプト。

Issue IDの形式や格納ディレクトリ名などを対話式で決定し、
`.aissue.json` に設定として書き出す。
"""

import json
import os

CONFIG_PATH = ".aissue.json"

ID_FORMATS = {
    "1": {"name": "sequential", "label": "連番(4桁ゼロ埋め)", "example": "0001, 0002, 0003"},
    "2": {"name": "date-sequential", "label": "日付+連番", "example": "20260719-01"},
    "3": {"name": "ulid", "label": "ULID", "example": "01ARZ3NDEKTSV4RRFFQ69G5FAV"},
}


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def choose_id_format():
    print("\nIssue IDの形式を選んでください:")
    for key, fmt in ID_FORMATS.items():
        print(f"  {key}) {fmt['label']}  例: {fmt['example']}")
    while True:
        choice = ask("番号で選択してください", default="1")
        if choice in ID_FORMATS:
            return ID_FORMATS[choice]["name"]
        print("1〜3の番号を入力してください。")


def is_inside_repo(path):
    repo_root = os.path.abspath(".")
    target = os.path.abspath(path)
    return target == repo_root or target.startswith(repo_root + os.sep)


def main():
    print("=== aissue セットアップ ===")

    if os.path.exists(CONFIG_PATH):
        overwrite = ask(f"{CONFIG_PATH} は既に存在します。上書きしますか? (y/N)", default="N")
        if overwrite.lower() != "y":
            print("セットアップを中止しました。")
            return

    id_format = choose_id_format()
    issues_dir = ask(
        "\nIssueを格納するディレクトリのパス(このリポジトリの外を推奨。"
        "誤コミット防止のため)",
        default="../aissue-data/issues",
    )
    if is_inside_repo(issues_dir):
        print(
            f"\n警告: '{issues_dir}' はこのリポジトリの中です。"
            "タスクデータを誤ってこのリポジトリにコミットしてしまう可能性があるため、"
            "リポジトリの外のパス(例: ../aissue-data/issues)を推奨します。"
        )
    attachments_dir = ask("添付ファイル用のサブディレクトリ名", default="attachments")

    config = {
        "id_format": id_format,
        "issues_dir": issues_dir,
        "attachments_dir": attachments_dir,
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    os.makedirs(issues_dir, exist_ok=True)

    print(f"\n{CONFIG_PATH} を作成しました:")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print(f"'{issues_dir}/' ディレクトリを作成しました(既存の場合はそのまま)。")
    print("\nセットアップ完了です。")


if __name__ == "__main__":
    main()
