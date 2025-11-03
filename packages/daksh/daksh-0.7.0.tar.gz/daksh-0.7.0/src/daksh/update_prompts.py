import shutil, json, os
from datetime import datetime
from pathlib import Path as P
from .__pre_init__ import cli


def current_file_dir(file: str) -> str:
    return P(file).parent.resolve()


def ls(folder: P) -> list[P]:
    return [f for f in folder.iterdir() if not f.name.startswith(".")]


def Info(msg: str):
    print(f"[INFO] {msg}")


def read_json(file: P) -> dict:
    with open(file, "r") as f:
        return json.load(f)


def write_json(file: P, data: dict):
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def read_lines(file: P) -> list[str]:
    with open(file, "r") as f:
        return f.readlines()


def append_lines(file: P, lines: list[str]):
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    if not file.exists():
        with open(file, "w") as f:
            pass
    with open(file, "a") as f:
        f.writelines(lines)


@cli.command()
def update_prompts(dry_run: bool = False):
    # Track files that are created/copied
    added_files = []

    def copy(src_fldr: P, dst_fldr: P):
        for f in ls(src_fldr):
            to = dst_fldr / f.name
            Info(f"Updating {f} to {to}")

            if dry_run:
                continue

            if f.is_file():
                shutil.copy(f, to)
                added_files.append(str(to))
            elif f.is_dir():
                shutil.copytree(f, to, dirs_exist_ok=True)
                added_files.append(str(to))

    # Try local assets first (for packaged version), then fall back to root assets (for development)
    cwd = current_file_dir(__file__)
    local_assets = cwd / "assets"
    root_assets = cwd.parent.parent / "assets"

    if root_assets.exists():
        assets_dir = root_assets
        Info("Using development assets from project root")
    elif local_assets.exists():
        assets_dir = local_assets
        Info("Using packaged assets")
    else:
        raise FileNotFoundError(
            "Assets directory not found in either local or root location"
        )

    # Remove existing .daksh folder before copying
    daksh_dest = P(".daksh")
    if daksh_dest.exists():
        Info("Removing existing .daksh folder")
        if not dry_run:
            shutil.rmtree(daksh_dest)

    copy(assets_dir / "daksh-prompts", daksh_dest)

    # Update .vscode/settings.json using template
    settings_path = P(".vscode/settings.json")
    settings_template = assets_dir / "json-files" / "settings.json"
    
    if settings_path.exists():
        settings = read_json(settings_path)
    else:
        settings = {}
    
    # Read template settings and merge
    if settings_template.exists():
        try:
            template_settings = read_json(settings_template)
            settings.update(template_settings)
        except Exception as e:
            Info(f"Warning: Could not parse template settings.json: {e}")
    else:
        # Fallback to manual construction if template doesn't exist
        chat_mode_files_locations = settings.get("chat.modeFilesLocations", {})
        chat_mode_files_locations[".daksh/prompts/**/"] = True
        settings["chat.modeFilesLocations"] = chat_mode_files_locations
    
    if not dry_run:
        write_json(settings_path, settings)
    added_files.append(str(settings_path))

    # Update .vscode/mcp.json using template
    mcp_path = P(".vscode/mcp.json")
    mcp_template = assets_dir / "json-files" / "mcp.json"
    
    if mcp_path.exists():
        mcp_config = read_json(mcp_path)
    else:
        mcp_config = {"servers": {}}
    
    # Read template mcp.json and merge servers
    if mcp_template.exists():
        try:
            template_mcp = read_json(mcp_template)
            if "servers" not in mcp_config:
                mcp_config["servers"] = {}
            # Merge servers from template
            mcp_config["servers"].update(template_mcp.get("servers", {}))
        except Exception as e:
            Info(f"Warning: Could not parse template mcp.json: {e}")
    
    if not dry_run:
        write_json(mcp_path, mcp_config)
    added_files.append(str(mcp_path))

    if os.path.exists(".github/copilot-instructions.md"):
        if (
            input(
                "Found an existing .github/copilot-instructions.md should we back it up? [y/N]: "
            ).lower()
            != "y"
        ):
            Info("Skipping backup")
        else:
            bkp = f".github/copilot-instructions.md.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            Info(f"Backing up existing .github/copilot-instructions.md to {bkp}")
            shutil.copy(".github/copilot-instructions.md", bkp)
            added_files.append(bkp)
    if not os.path.exists(".github"):
        os.makedirs(".github")
    shutil.copy(
        assets_dir / "copilot-instructions.md", ".github/copilot-instructions.md"
    )
    added_files.append(".github/copilot-instructions.md")

    shutil.copy(assets_dir / "mkdocs.yml", "mkdocs.yml")
    added_files.append("mkdocs.yml")

    shutil.copy(assets_dir / "mkdocs_deps.txt", "mkdocs_deps.txt")
    added_files.append("mkdocs_deps.txt")

    shutil.copy(assets_dir / "run-mkdocs.sh", "run-mkdocs.sh")
    added_files.append("run-mkdocs.sh")

    # shutil.copy(assets_dir / "mcp_deps.txt", "mcp_deps.txt")
    # added_files.append("mcp_deps.txt")


    os.makedirs("docs/overrides", exist_ok=True)
    shutil.copy(assets_dir / "extra.css", "docs/overrides/extra.css")
    added_files.append("docs/overrides/extra.css")

    shutil.copytree(assets_dir / "overrides", "./overrides", dirs_exist_ok=True)
    added_files.append("./overrides")

    # # Copy fastMcp folder
    # if not dry_run:
    #     shutil.copytree(assets_dir / "fastMcp", "./fastMcp", dirs_exist_ok=True)
    # added_files.append("./fastMcp")

    if not os.path.exists("docs/index.md"):
        shutil.copy(assets_dir / "index.md", "docs/index.md")
        added_files.append("docs/index.md")

    # Ensure mkdocs helper files (if present in assets) are copied
    for helper in ["mkdocs_deps.txt", "run-mkdocs.sh"]:
        src_helper = assets_dir / helper
        if src_helper.exists():
            Info(f"Adding helper asset {src_helper} -> {helper}")
            if not dry_run:
                shutil.copy(src_helper, helper)
                if helper.endswith('.sh'):
                    os.chmod(helper, 0o755)
            added_files.append(helper)

    # Create or update .vscode/tasks.json using template
    tasks_json_path = P('.vscode/tasks.json')
    tasks_template = assets_dir / "json-files" / "tasks.json"
    
    if tasks_json_path.exists():
        try:
            existing_tasks = read_json(tasks_json_path)
        except Exception:
            existing_tasks = {"version": "2.0.0", "tasks": []}
    else:
        existing_tasks = {"version": "2.0.0", "tasks": []}
    
    # Read template tasks.json and use it as base
    if tasks_template.exists():
        try:
            template_tasks = read_json(tasks_template)
            # Use template as base, but preserve any existing custom tasks if needed
            final_tasks = template_tasks
        except Exception as e:
            Info(f"Warning: Could not parse template tasks.json: {e}")
            # Fallback to manual construction
            final_tasks = {
                "version": "2.0.0",
                "tasks": [
                    {
                        "label": "Run MkDocs",
                        "type": "shell",
                        "command": "chmod +x ./run-mkdocs.sh && ./run-mkdocs.sh",
                        "problemMatcher": [],
                        "group": {"kind": "build", "isDefault": True},
                    }
                ],
            }
    else:
        # Fallback to manual construction if template doesn't exist
        final_tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Run MkDocs",
                    "type": "shell",
                    "command": "chmod +x ./run-mkdocs.sh && ./run-mkdocs.sh",
                    "problemMatcher": [],
                    "group": {"kind": "build", "isDefault": True},
                }
            ],
        }
    
    if not dry_run:
        if not tasks_json_path.parent.exists():
            tasks_json_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(tasks_json_path, final_tasks)
    added_files.append(str(tasks_json_path))

    # Display summary of added files
    print("\n📁 Files added to current working directory:")
    for file in added_files:
        print(f"   ✓ {file}")
    print(f"\nTotal: {len(added_files)} files/directories added or updated\n")
