import sys, os, re

def setup(repo_url: str | None = None):
    """
    Normalise notebook environment:
    - In Colab: clone/checkout correct branch, add repo root to sys.path, cd to notebook folder
    - In local Jupyter: detect notebook path, find repo root, add sys.path, cd to notebook folder
    - Optionally: if repo_url is provided, skip metadata lookup and clone that repo directly
    """
    try:
        import google.colab
        from google.colab import _message
        is_colab = True
    except ImportError:
        is_colab = False

    if is_colab:
        # --- Colab case ---
        org = repo = branch = nb_relpath = None

        # 🔹 Only attempt to read notebook metadata if no repo_url is given
        if not repo_url:
            nb_request = _message.blocking_request('get_ipynb')
            nb = nb_request['ipynb'] if nb_request and 'ipynb' in nb_request else None

            if nb:
                for cell in nb['cells']:
                    if cell.get('cell_type') == 'markdown':
                        text = "".join(cell.get('source', []))
                        href_match = re.search(r'href="([^"]+)"', text)
                        if href_match:
                            href = href_match.group(1)
                            m = re.search(
                                r'github/([^/]+)/([^/]+)/blob/([^/]+)/(.*?)(?:\.ipynb|#|$)',
                                href
                            )
                            if m:
                                org, repo, branch, nb_relpath = m.groups()
                                break

        # ---- If no metadata or user provided URL, fallback to repo_url ----
        if repo_url and not repo:
            m = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if not m:
                raise ValueError(f"Invalid GitHub repo URL: {repo_url}")
            org, repo = m.groups()
            branch = None
            nb_relpath = ""
        elif not repo:
            raise RuntimeError(
                "No Colab badge or notebook metadata found.\n"
                "Please supply a repo URL, e.g.:\n"
                "  setup('https://github.com/org/repo')"
            )

        repo_root = f"/content/{repo}"

        # Clone or checkout branch
        if not os.path.exists(repo_root):
            if branch:
                os.system(f"git clone -b {branch} https://github.com/{org}/{repo}.git {repo_root}")
            else:
                os.system(f"git clone https://github.com/{org}/{repo}.git {repo_root}")
        else:
            if branch:
                os.system(f"cd {repo_root} && git fetch && git checkout {branch}")
            else:
                os.system(f"cd {repo_root} && git fetch")

        # Add repo root to sys.path
        sys.path.insert(0, repo_root)

        # cd into the notebook’s directory
        target_dir = os.path.join(repo_root, os.path.dirname(nb_relpath)) if nb_relpath else repo_root
        os.chdir(target_dir)

        print(f"[Colab] Repo: {repo} | Branch: {branch}")
        print("[Colab] Repo root added to sys.path")
        print(f"[Colab] Working directory set to: {os.path.relpath(target_dir, repo_root)}")

        return repo_root, branch, target_dir

    else:
        # --- Local Jupyter case ---
        import ipynbname
        from pathlib import Path

        nb_path = ipynbname.path()
        nb_dir = nb_path.parent

        # Walk up until we find repo root (by `.git`)
        repo_root = nb_dir
        while not (repo_root / ".git").exists() and repo_root != repo_root.parent:
            repo_root = repo_root.parent

        sys.path.insert(0, str(repo_root))
        os.chdir(nb_dir)

        print("[Local] Repo root added to sys.path")
        print(f"[Local] Working directory set to: {os.path.relpath(nb_dir, repo_root)}")

        return str(repo_root), None, str(nb_dir)
