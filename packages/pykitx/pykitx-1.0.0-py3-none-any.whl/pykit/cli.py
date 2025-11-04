import argparse
from .scaffolder import scaffold
from . import __version__

def main():
    parser = argparse.ArgumentParser(
        prog="pykit",
        description="PyKit - modern Python project initializer"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show PyKit version and exit"
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="Create a new Python project")
    p_new.add_argument("name", help="Project name")
    p_new.add_argument("-l", "--license", default="MIT", help="License (default: MIT)")
    p_new.add_argument("-ty", "--type", choices=["pkg", "app"], default="pkg", help="Project type")
    p_new.add_argument("-ig","--init-git", action="store_true", help="Initialize git repository")
    p_new.add_argument("--desc", default="A Python project", help="Project description")
    p_new.add_argument("--author", default="Your-Brand/Name", help="Author name")
    p_new.add_argument("--email", default="dummy@mail.com", help="Author email")
    p_new.add_argument("--url", help="Project website")
    p_new.add_argument("--repo", help="GitHub repository (e.g. rillToMe/pykit)")
    p_new.add_argument("--force", action="store_true", help="Overwrite existing folder")
    p_new.add_argument(
        "-T", "--template",
        choices=["cli-stdlib", "cli-typer", "web-fastapi", "web-flask", "cli-click", "tui-rich"],
        default="cli-stdlib",
        help="Project template for main.py"
    )
    p_new.set_defaults(cmd="new")

    p_about = sub.add_parser("about", help="Show information about PyKit")
    p_about.set_defaults(cmd="about")

    p_info = sub.add_parser("info", help="Alias of 'about'")
    p_info.set_defaults(cmd="about")

    args = parser.parse_args()

    if args.cmd == "new":
        scaffold(
            name=args.name,
            license_id=args.license,
            proj_type=args.type,
            init_git=args.init_git,
            description=args.desc,
            author=args.author,
            email=args.email,
            url=args.url,
            repo=args.repo,
            force=args.force,
            template=args.template,
        )

    elif args.cmd == "about":
        from .info import show_about
        show_about()
