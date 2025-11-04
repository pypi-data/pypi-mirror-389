from pathlib import Path
from string import Template
import json, sys, subprocess, datetime, pkgutil
from importlib.resources import files

def _load_text(resource_path: str) -> str:
    try:
        return (files("pykit") / "templates" / resource_path).read_text(encoding="utf-8")
    except Exception:
        pass

    try:
        data = pkgutil.get_data("pykit", f"templates/{resource_path}")
        if data is not None:
            return data.decode("utf-8")
    except Exception:
        pass

    here = Path(__file__).resolve().parent
    local = here / "templates" / resource_path
    if local.exists():
        return local.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Template not found: {resource_path}")

def _load_licenses():
    text = _load_text("licenses.json")
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or not data:
            raise ValueError("licenses.json must be a non-empty JSON object")
        return data
    except Exception as e:
        print(f"[!] Failed to load licenses.json: {e}", file=sys.stderr)
        return {
            "MIT": "MIT License\n\nCopyright (c) {year} {author}\n\nPermission is hereby granted... (singkat)"
        }

def scaffold(name, license_id, proj_type, init_git, description, author, email, url, repo, force, template):
    root = Path(name)
    if root.exists() and not force:
        print(f"[!] Folder '{name}' Already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    package = name.replace("-", "_")
    src_pkg_dir = root / "src" / package
    tests_dir = root / "tests"
    src_pkg_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    licenses = _load_licenses()
    if license_id not in licenses:
        print(f"[!] License '{license_id}' Not recognized. Using MIT as default.")
        license_id = "MIT"
    license_text = licenses[license_id].format(
        year=datetime.datetime.now().year,
        author=author,
        project=name,
    )
    (root / "LICENSE").write_text(license_text, encoding="utf-8")

    readme_tmpl = Template(_load_text("README.md.tmpl"))
    readme = readme_tmpl.substitute(
        project_name=name,
        description=description,
        cli_name=name,
        license=license_id,
    )
    (root / "README.md").write_text(readme, encoding="utf-8")

    deps = ""
    if template == "cli-typer":
        deps = 'dependencies = ["typer>=0.12"]'
    elif template == "web-fastapi":
        deps = 'dependencies = ["fastapi>=0.115", "uvicorn[standard]>=0.30", "jinja2>=3.1", "aiofiles>=23.2"]'
    elif template == "web-flask":
        deps = 'dependencies = ["flask>=3.0"]'
    elif template == "cli-click":
        deps = 'dependencies = ["click>=8.1"]'
    elif template == "tui-rich":
        deps = 'dependencies = ["rich>=13.7"]'
        
    extra_setuptools = ""
    if template in ("web-flask", "web-fastapi"):
        extra_setuptools = f"""
    [tool.setuptools]
    include-package-data = true

    [tool.setuptools.package-data]
    {package} = ["templates/**/*.html", "static/**/*"]
    """.strip()

    pyproj_tmpl = Template(_load_text("pyproject.toml.tmpl"))
    pyproj = pyproj_tmpl.substitute(
        project_name=name,
        description=description,
        author=author,
        email=email,
        package=package,
        license=license_id,
        dependencies=deps,
        extra_setuptools=extra_setuptools,
    )
    (root / "pyproject.toml").write_text(pyproj, encoding="utf-8")

    (root / ".gitignore").write_text(_load_text("gitignore.tmpl"), encoding="utf-8")

    (src_pkg_dir / "__init__.py").write_text(
        '__all__ = []\n__version__ = "0.1.0"\n', encoding="utf-8"
    )

    tmpl_map = {
        "cli-stdlib": "main_cli_stdlib.py.tmpl",
        "cli-typer": "main_cli_typer.py.tmpl",
        "web-fastapi": "main_web_fastapi.py.tmpl",
        "web-flask": "main_web_flask.py.tmpl", 
        "cli-click": "main_cli_click.py.tmpl",
        "tui-rich": "main_tui_rich.py.tmpl",
    }
    tmpl_name = tmpl_map.get(template, "main_cli_stdlib.py.tmpl")
    main_raw = _load_text(tmpl_name)
    main_code = Template(main_raw).safe_substitute(project_name=name, package=package)
    if template == "web-fastapi":
       
        main_code = main_code.replace("{{package}}", package)
    
    if template == "web-flask":
        tpl_dir    = src_pkg_dir / "templates"
        static_dir = src_pkg_dir / "static"
        (tpl_dir).mkdir(parents=True, exist_ok=True)
        (static_dir / "css").mkdir(parents=True, exist_ok=True)
        (static_dir / "js").mkdir(parents=True, exist_ok=True)
        (static_dir / "img").mkdir(parents=True, exist_ok=True)

        (tpl_dir / "base.html").write_text(_load_text("flask_base.html.tmpl"), encoding="utf-8")
        (tpl_dir / "404.html").write_text(_load_text("flask_404.html.tmpl"), encoding="utf-8")

        (static_dir / "css" / "styles.css").write_text(_load_text("flask_styles.css.tmpl"), encoding="utf-8")
        (static_dir / "js" / "app.js").write_text(_load_text("flask_app_js.tmpl"), encoding="utf-8")
        (static_dir / "img" / "logo.svg").write_text(_load_text("logo.svg.tmpl"), encoding="utf-8")
        (static_dir / "img" / "favicon.svg").write_text(_load_text("favicon.svg.tmpl"), encoding="utf-8")
        
    if template == "web-fastapi":
        tpl_dir    = src_pkg_dir / "templates"
        static_dir = src_pkg_dir / "static"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        (static_dir / "css").mkdir(parents=True, exist_ok=True)
        (static_dir / "js").mkdir(parents=True, exist_ok=True)
        (static_dir / "img").mkdir(parents=True, exist_ok=True)
        (tpl_dir / "base.html").write_text(_load_text("fastapi_base.html.tmpl"), encoding="utf-8")
        (tpl_dir / "404.html").write_text(_load_text("fastapi_404.html.tmpl"), encoding="utf-8")
        (static_dir / "css" / "styles.css").write_text(_load_text("fastapi_styles.css.tmpl"), encoding="utf-8")
        (static_dir / "js"  / "app.js").write_text(_load_text("fastapi_app_js.tmpl"), encoding="utf-8")
        (static_dir / "img" / "logo.svg").write_text(_load_text("logo.svg.tmpl"), encoding="utf-8")
        (static_dir / "img" / "favicon.svg").write_text(_load_text("favicon.svg.tmpl"), encoding="utf-8")

    (src_pkg_dir / "main.py").write_text(main_code, encoding="utf-8")
    
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    ci_path = root / ".github" / "workflows"
    ci_path.mkdir(parents=True, exist_ok=True)
    (ci_path / "ci.yml").write_text(_load_text("ci_github.yml.tmpl"), encoding="utf-8")

    if init_git:
        subprocess.run(["git", "init"], cwd=root, check=False)
        subprocess.run(["git", "add", "-A"], cwd=root, check=False)
        subprocess.run(["git", "commit", "-m", "chore: scaffold with PyKit"], cwd=root, check=False)

    (root / ".env.example").write_text("# Example environment variables\n", encoding="utf-8")

    deps_list = []
    if template == "cli-typer":
        deps_list = ["typer>=0.12"]
    elif template == "web-fastapi":
        deps_list = ["fastapi>=0.115", "uvicorn[standard]>=0.30", "jinja2>=3.1", "aiofiles>=23.2"]
    elif template == "web-flask":
        deps_list = ["flask>=3.0"]
    elif template == "cli-click":
        deps_list = ["click>=8.1"]
    elif template == "tui-rich":
        deps_list = ["rich>=13.7"]

    req_file = root / "requirements.txt"
    if deps_list:
        req_text = "\n".join(deps_list) + "\n"
        req_file.write_text(req_text, encoding="utf-8")
    else:
        req_file.write_text("# no external dependencies\n", encoding="utf-8")

    print(f"\n[✓] Project '{name}' Successfully created in {root.resolve()}")
    print("─────────────────────────────────────────────")
    print("Next steps:")
    print(f"  cd {name}")
    print("  pip install -e.")
    print("  # or for quick setup:")
    print("  pip install -r requirements.txt")
    print(f"  {name}")
    print("─────────────────────────────────────────────\n")
