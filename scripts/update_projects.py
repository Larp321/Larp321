"""Rebuild the project list in README.md from the owner's public GitHub repositories.

Runs daily in GitHub Actions (.github/workflows/update-projects.yml), so every new
public repo appears on the profile automatically. Only the text between the
PROJECTS:START / PROJECTS:END markers is replaced; the rest of the README is
written by hand.

    python scripts/update_projects.py            # uses GITHUB_TOKEN if set
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime

OWNER = os.environ.get("PROFILE_OWNER", "Larp321")
README = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner&sort=pushed"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "profile-readme-updater"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def demo_link(repo):
    if repo.get("homepage"):
        return repo["homepage"]
    if repo.get("has_pages"):
        return f"https://{OWNER.lower()}.github.io/{repo['name']}/"
    return None


def render(repos):
    repos = [r for r in repos
             if not r["fork"] and not r["archived"] and not r["private"] and r["name"].lower() != OWNER.lower()]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    if not repos:
        return "_No public projects yet._"
    rows = ["| Project | What it is | Built with | Links |", "|---|---|---|---|"]
    for r in repos:
        desc = (r.get("description") or "").replace("|", "\\|").strip() or "–"
        lang = r.get("language") or "–"
        links = [f"[code]({r['html_url']})"]
        if demo_link(r):
            links.append(f"[live demo]({demo_link(r)})")
        updated = datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y")
        rows.append(f"| **[{r['name']}]({r['html_url']})** | {desc} | {lang} | {' · '.join(links)}<br><sub>updated {updated}</sub> |")
    return "\n".join(rows) + "\n\n<sub>This list updates itself daily from my public repositories.</sub>"


def main():
    text = open(README, encoding="utf-8").read()
    if START not in text or END not in text:
        sys.exit("README.md is missing the PROJECTS markers")
    block = f"{START}\n{render(fetch_repos())}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        open(README, "w", encoding="utf-8", newline="\n").write(new)
        print("README.md updated")
    else:
        print("no changes")


if __name__ == "__main__":
    main()
