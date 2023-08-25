"""Update the site by importing content from the folder."""
import argparse
import logging
import os
import subprocess
from datetime import datetime


def py_str(cstr):
    return cstr.decode("utf-8")


# list of files to skip
skip_list = {
    ".gitignore",
    ".nojekyll",
    "CNAME",
    "README.md",
    "LICENSE",
}


def main():
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description="Deploy a built html to the root.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--site-path", type=str)
    parser.add_argument("--source-path", type=str, default="_build/html")

    args = parser.parse_args()

    def run_cmd(cmd):
        proc = subprocess.Popen(
            cmd, cwd=args.site_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        (out, _) = proc.communicate()
        if proc.returncode != 0:
            msg = f"cmd error: {cmd}"
            msg += py_str(out)
            raise RuntimeError(msg)
        return py_str(out)

    run_cmd(["git", "config", "user.name", "mlc-bot"])
    run_cmd(["git", "config", "user.email", "106439794+mlc-bot@users.noreply.github.com"])
    run_cmd(["git", "fetch"])
    run_cmd(["git", "checkout", "-B", "gh-pages", "origin/gh-pages"])
    files = run_cmd(["git", "ls-files"])
    skip_set = set(skip_list)

    for fname in files.split("\n"):
        fname = fname.strip()
        if fname and fname not in skip_set:
            if not args.dry_run:
                run_cmd(["rm", "-rf", fname])
            print(f"Remove {fname}")

    os.system(f"cp -rf {args.source_path}/* {args.site_path}")
    run_cmd(["git", "add", "--all"])
    print(run_cmd(["git", "status"]))

    if not args.dry_run:
        try:
            run_cmd(["git", "commit", "-am", f" Update at {datetime.now()}"])
        except RuntimeError as e:
            print(e)
        print(run_cmd(["git", "push", "origin", "gh-pages"]))
        print("Finish updating and push to origin/gh-pages ...")


if __name__ == "__main__":
    main()
