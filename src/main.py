import json
import os
import sys

import config
import renderer
from github_api import GitHubClient, collect_stats


def main() -> int:
    if not config.USERNAME:
        print("[error] GH_USERNAME is not set", file=sys.stderr)
        return 1
    if not config.TOKEN:
        print("[warn] no token found, using the anonymous rate limit", file=sys.stderr)

    client = GitHubClient()
    print(f"[info] collecting stats for @{client.username} ...")
    stats = collect_stats(client)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    stats_path = os.path.join(config.OUTPUT_DIR, config.STATS_IMAGE)
    langs_path = os.path.join(config.OUTPUT_DIR, config.LANGS_IMAGE)

    renderer.render_stats_card(stats, stats_path)
    renderer.render_language_card(stats, langs_path)

    with open(os.path.join(config.OUTPUT_DIR, "stats.json"), "w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)

    print(f"[info] written {stats_path}")
    print(f"[info] written {langs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
