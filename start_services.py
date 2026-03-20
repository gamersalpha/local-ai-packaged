#!/usr/bin/env python3
"""
start_services.py
Deployment orchestrator for Local AI Packaged.

Features:
- Interactive setup wizard (--setup)
- Selective service deployment (--services)
- SWAG reverse proxy auto-detection (--proxy)
- Supabase and Caddy management in docker-compose.yml
- .env validation / auto-generation
- Dry-run mode, image update, profile selection
"""

import os
import subprocess
import shutil
import time
import argparse
import sys
import glob as globmod


# ---------------------- CONSTANTS ---------------------- #

# Service dependency map: service -> list of infrastructure services it requires
SERVICE_DEPS = {
    "n8n":       ["postgres", "redis"],
    "n8n-import": ["postgres"],
    "flowise":   [],
    "open-webui": ["searxng"],
    "qdrant":    [],
    "neo4j":     [],
    "searxng":   ["redis"],
    "langfuse-web":    ["postgres", "redis", "clickhouse", "minio"],
    "langfuse-worker": ["postgres", "redis", "clickhouse", "minio"],
    "clickhouse": [],
    "minio":     [],
    "postgres":  [],
    "redis":     [],
    "unsloth":   [],
}

# Friendly name -> list of compose service names
SERVICE_GROUPS = {
    "n8n":       ["n8n", "n8n-import"],
    "openwebui": ["open-webui"],
    "flowise":   ["flowise"],
    "qdrant":    ["qdrant"],
    "neo4j":     ["neo4j"],
    "langfuse":  ["langfuse-web", "langfuse-worker", "clickhouse", "minio"],
    "searxng":   ["searxng"],
    "unsloth":   ["unsloth"],
}

ALL_SELECTABLE = list(SERVICE_GROUPS.keys()) + ["ollama"]


# ---------------------- UTILS ---------------------- #

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def confirm(prompt):
    """Ask the user to confirm with OK or cancel."""
    while True:
        choice = input(f"\n{prompt} (OK / cancel): ").strip().lower()
        if choice in ["ok", "o", "y", "yes"]:
            return True
        elif choice in ["cancel", "c", "n", "no"]:
            print("Operation cancelled.")
            sys.exit(0)
        else:
            print("Please type OK or cancel.")


def detect_gpu_type():
    """Detect GPU hardware."""
    if shutil.which("nvidia-smi"):
        return "nvidia"
    if shutil.which("rocm-smi") or os.path.isdir("/opt/rocm"):
        return "amd"
    return "cpu"


# ---------------------- PROXY DETECTION ---------------------- #

def detect_swag():
    """Detect if SWAG reverse proxy is running or installed."""
    # Check running containers
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=swag", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        )
        if "swag" in result.stdout.lower():
            return True
    except Exception:
        pass

    # Check common SWAG config paths
    swag_paths = [
        os.path.expanduser("~/swag/nginx/proxy-confs"),
        "/etc/swag/nginx/proxy-confs",
        "/volume1/docker/swag/nginx/proxy-confs",   # Synology
        "/mnt/user/appdata/swag/nginx/proxy-confs",  # Unraid
    ]
    for p in swag_paths:
        if os.path.isdir(p):
            return True

    return False


def find_swag_proxy_dir():
    """Find the SWAG proxy-confs directory."""
    candidates = [
        os.path.expanduser("~/swag/nginx/proxy-confs"),
        "/etc/swag/nginx/proxy-confs",
        "/volume1/docker/swag/nginx/proxy-confs",
        "/mnt/user/appdata/swag/nginx/proxy-confs",
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p

    # Try to find via docker inspect
    try:
        result = subprocess.run(
            ["docker", "inspect", "swag", "--format",
             "{{range .Mounts}}{{if eq .Destination \"/config\"}}{{.Source}}{{end}}{{end}}"],
            capture_output=True, text=True, check=True
        )
        config_path = result.stdout.strip()
        if config_path:
            proxy_dir = os.path.join(config_path, "nginx", "proxy-confs")
            if os.path.isdir(proxy_dir):
                return proxy_dir
    except Exception:
        pass

    return None


def install_swag_confs(swag_proxy_dir):
    """Copy SWAG proxy-conf templates to the SWAG proxy-confs directory."""
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swag")
    if not os.path.isdir(templates_dir):
        print("  swag/ templates directory not found, skipping.")
        return

    installed = 0
    for conf_file in sorted(os.listdir(templates_dir)):
        if not conf_file.endswith(".conf"):
            continue
        src = os.path.join(templates_dir, conf_file)
        dst = os.path.join(swag_proxy_dir, conf_file)
        shutil.copyfile(src, dst)
        print(f"  Installed {conf_file}")
        installed += 1

    if installed > 0:
        print(f"  {installed} proxy configs installed to {swag_proxy_dir}")
        # Restart SWAG to pick up new configs
        try:
            run_command(["docker", "restart", "swag"])
            print("  SWAG restarted to apply new configs.")
        except Exception:
            print("  Could not restart SWAG container. Restart it manually.")


# ---------------------- ENV MANAGEMENT ---------------------- #

def check_or_generate_env():
    """Check if .env exists. If not, offer to generate it."""
    env_path = ".env"
    if os.path.exists(env_path):
        print(".env file detected.")
        return True
    else:
        print("No .env file detected!")
        print("Without it, Docker will raise many missing variable warnings.")
        choice = input("\nDo you want to generate one now using generate_env.py? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            if not os.path.exists("generate_env.py"):
                print("generate_env.py not found in current directory.")
                sys.exit(1)
            print("Generating .env file with sensitive values...")
            run_command(["python3", "generate_env.py", "--yes", "--regen-sensitive"])
            print(".env generated successfully.")
            return True
        else:
            print("Aborting. You must have a valid .env file to continue.")
            sys.exit(1)


# ---------------------- YAML MODIFIERS ---------------------- #

def toggle_supabase_include(disable_supabase: bool):
    """(Un)comment the supabase include block in docker-compose.yml.

    When disabling, comments out both the 'include:' directive and the supabase path.
    When enabling, restores both lines so Docker Compose can parse the include block.
    """
    compose_path = "docker-compose.yml"
    if not os.path.exists(compose_path):
        print("docker-compose.yml not found, skipping Supabase include management.")
        return

    with open(compose_path, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # Handle the 'include:' directive itself
        if "supabase/docker/docker-compose.yml" not in stripped:
            if stripped == "include:" and disable_supabase:
                new_lines.append("# " + line if not line.startswith("#") else line)
                if not line.startswith("#"):
                    modified = True
                continue
            elif stripped in ("# include:", "#include:") and not disable_supabase:
                new_lines.append(line.lstrip("#").lstrip(" ") if stripped.startswith("#") else line)
                # Restore: remove leading '# '
                restored = line
                if restored.startswith("# "):
                    restored = restored[2:]
                elif restored.startswith("#"):
                    restored = restored[1:]
                new_lines[-1] = restored
                modified = True
                continue

        # Handle the supabase compose path line
        if "supabase/docker/docker-compose.yml" in stripped:
            if disable_supabase and not stripped.startswith("#"):
                new_lines.append("# " + line)
                modified = True
            elif not disable_supabase and stripped.startswith("#"):
                restored = line
                if restored.strip().startswith("# "):
                    restored = restored.replace("# ", "", 1)
                elif restored.strip().startswith("#"):
                    restored = restored.replace("#", "", 1)
                new_lines.append(restored)
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        with open(compose_path, "w") as f:
            f.writelines(new_lines)
        state = "disabled (include block commented)" if disable_supabase else "enabled (include block restored)"
        print(f"Supabase {state} in docker-compose.yml.")
    else:
        if disable_supabase:
            print("Supabase include already disabled in docker-compose.yml.")


def toggle_caddy_service(disable_caddy: bool):
    """(Un)comment the caddy service block in docker-compose.yml."""
    compose_path = "docker-compose.yml"
    if not os.path.exists(compose_path):
        print("docker-compose.yml not found, skipping Caddy management.")
        return

    with open(compose_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    modified = False
    in_caddy_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("caddy:"):
            in_caddy_block = True
            if disable_caddy and not line.startswith("#"):
                new_lines.append("# " + line)
                modified = True
            elif not disable_caddy and line.startswith("#"):
                new_lines.append(line.replace("# ", "", 1))
                modified = True
            else:
                new_lines.append(line)
            continue

        if in_caddy_block:
            if not stripped or not line.startswith(" "):
                in_caddy_block = False
                new_lines.append(line)
                continue

            if disable_caddy and not line.startswith("#"):
                new_lines.append("# " + line)
                modified = True
            elif not disable_caddy and line.startswith("#"):
                new_lines.append(line.replace("# ", "", 1))
                modified = True
            else:
                new_lines.append(line)
            continue

        new_lines.append(line)

    if modified:
        with open(compose_path, "w") as f:
            f.writelines(new_lines)
        state = "commented out" if disable_caddy else "restored"
        print(f"Caddy service {state} in docker-compose.yml.")


# ---------------------- SEARXNG ---------------------- #

def generate_searxng_secret_key():
    """Generate a secret key for SearXNG."""
    settings_path = os.path.join("searxng", "settings.yml")
    base_path = os.path.join("searxng", "settings-base.yml")

    if not os.path.exists(base_path):
        print("Base settings not found, skipping SearXNG key generation.")
        return

    if not os.path.exists(settings_path):
        print("Creating settings.yml from base...")
        shutil.copyfile(base_path, settings_path)

    print("Generating SearXNG secret key...")
    try:
        random_key = subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode().strip()
        sed_cmd = ["sed", "-i", f"s|ultrasecretkey|{random_key}|g", settings_path]
        subprocess.run(sed_cmd, check=True)
        print("SearXNG secret key generated.")
    except Exception as e:
        print(f"Error generating key: {e}")


# ---------------------- SERVICE RESOLUTION ---------------------- #

def resolve_services(selected_services):
    """Resolve selected service groups into a list of compose service names with deps."""
    compose_services = set()

    for svc in selected_services:
        if svc == "ollama":
            continue  # handled via profiles
        if svc in SERVICE_GROUPS:
            for s in SERVICE_GROUPS[svc]:
                compose_services.add(s)
                # Add dependencies
                for dep in SERVICE_DEPS.get(s, []):
                    compose_services.add(dep)

    return sorted(compose_services)


# ---------------------- DOCKER ACTIONS ---------------------- #

def stop_existing_containers(profile=None):
    """Stop existing containers for the project."""
    print("Stopping existing containers for project 'localai'...")
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml", "down"])
    try:
        run_command(cmd)
    except subprocess.CalledProcessError:
        print("Docker compose down returned a non-zero exit code. Continuing.")


def build_compose_base(profile=None, environment=None, supabase_enabled=False):
    """Build the base docker compose command with profile and environment."""
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml"])
    if environment == "private":
        cmd.extend(["-f", "docker-compose.override.private.yml"])
    elif environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.yml"])
        if supabase_enabled and os.path.exists("docker-compose.override.public.supabase.yml"):
            cmd.extend(["-f", "docker-compose.override.public.supabase.yml"])
    return cmd


def start_local_ai(profile=None, environment=None, services=None, supabase_enabled=False):
    """Start local AI stack service by service, collecting results."""
    print("\nStarting Local AI stack...")

    base_cmd = build_compose_base(profile, environment, supabase_enabled=supabase_enabled)

    # If "all", launch everything at once first (fast path)
    if not services or "all" in services:
        service_list = None
    else:
        service_list = resolve_services(services)

    # Try launching everything at once (output streamed in real-time)
    cmd = base_cmd + ["up", "-d"]
    if service_list:
        cmd.extend(service_list)

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print_deployment_summary(base_cmd)
        return

    print("\nSome services failed to start. Retrying individually...\n")

    # Get the list of services to start
    if not service_list:
        # Get all services from compose config
        try:
            config_cmd = base_cmd + ["config", "--services"]
            config_result = subprocess.run(config_cmd, capture_output=True, text=True, check=True)
            service_list = [s.strip() for s in config_result.stdout.strip().split("\n") if s.strip()]
        except subprocess.CalledProcessError:
            print("Could not list services from compose config.")
            return

    # Infrastructure first, then apps
    infra_services = ["postgres", "redis", "clickhouse", "minio"]
    ordered = []
    for svc in infra_services:
        if svc in service_list:
            ordered.append(svc)
    for svc in service_list:
        if svc not in ordered:
            ordered.append(svc)

    succeeded = []
    failed = []
    skipped = []

    for svc in ordered:
        # Check if already running
        check = subprocess.run(
            ["docker", "ps", "--filter", f"name=^{svc}$", "--filter", "status=running", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        if svc in check.stdout:
            skipped.append(svc)
            continue

        # Try to start
        svc_cmd = base_cmd + ["up", "-d", "--no-deps", svc]
        print(f"  Starting {svc}...")
        svc_result = subprocess.run(svc_cmd, capture_output=True, text=True)

        if svc_result.returncode == 0:
            succeeded.append(svc)
        else:
            # Extract short error message
            err = svc_result.stderr.strip().split("\n")[-1] if svc_result.stderr else "unknown error"
            failed.append((svc, err))
            print(f"    FAILED: {err}")

    # Print summary
    print("\n" + "=" * 50)
    print("  DEPLOYMENT REPORT")
    print("=" * 50)

    if skipped:
        print(f"\n  Already running ({len(skipped)}):")
        for svc in skipped:
            print(f"    [RUNNING] {svc}")

    if succeeded:
        print(f"\n  Started successfully ({len(succeeded)}):")
        for svc in succeeded:
            print(f"    [OK]      {svc}")

    if failed:
        print(f"\n  Failed ({len(failed)}):")
        for svc, err in failed:
            print(f"    [FAIL]    {svc}: {err}")

    print("\n" + "=" * 50)

    if failed:
        print(f"\n  {len(failed)} service(s) failed. Check logs with: docker logs <service_name>")
    else:
        print("\n  All services deployed successfully!")

    print("")


def print_deployment_summary(base_cmd):
    """Print a summary of running containers."""
    print("\n" + "=" * 50)
    print("  DEPLOYMENT REPORT")
    print("=" * 50)

    result = subprocess.run(
        ["docker", "ps", "--filter", "label=com.docker.compose.project=localai",
         "--format", "table {{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print(result.stdout)
    else:
        # Fallback: show all running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True, text=True
        )
        print(result.stdout)

    print("=" * 50)


def clone_supabase_repo():
    """Clone the Supabase repository using sparse checkout if not already present."""
    if not os.path.exists("supabase"):
        print("Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git"
        ])
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
    else:
        print("Supabase repository already exists, updating...")
        os.chdir("supabase")
        run_command(["git", "pull"])
        os.chdir("..")


def prepare_supabase_env():
    """Copy .env from root to supabase/docker/.env."""
    src = ".env"
    dst = os.path.join("supabase", "docker", ".env")
    if os.path.exists(src):
        print("Copying root .env to supabase/docker/.env ...")
        shutil.copyfile(src, dst)
    else:
        print("No .env found at root. Supabase will fail without it.")


# ---------------------- INTERACTIVE SETUP ---------------------- #

def interactive_setup():
    """Interactive service selection wizard for first-time setup."""
    print("")
    print("=" * 48)
    print("   Local AI Packaged — Interactive Setup")
    print("=" * 48)
    print("")

    # Hardware detection
    gpu = detect_gpu_type()
    profile_map = {"nvidia": "gpu-nvidia", "amd": "gpu-amd", "cpu": "cpu"}
    detected_profile = profile_map[gpu]
    print(f"Detected hardware: {gpu.upper()} -> profile '{detected_profile}'")
    override = input(f"Use this profile? (Enter = yes, or type cpu/gpu-nvidia/gpu-amd): ").strip()
    if override in profile_map.values():
        detected_profile = override
    print("")

    # Service selection
    available = [
        ("ollama",    "Ollama      — Local LLM inference",      True),
        ("openwebui", "Open WebUI  — Chat interface",           True),
        ("n8n",       "n8n         — Workflow automation",      True),
        ("flowise",   "Flowise     — Low-code AI builder",      False),
        ("qdrant",    "Qdrant      — Vector database",          True),
        ("neo4j",     "Neo4j       — Graph database",           False),
        ("langfuse",  "Langfuse    — LLM observability",        False),
        ("searxng",   "SearXNG     — Web search for RAG",       True),
        ("unsloth",   "Unsloth     — LLM fine-tuning studio",   False),
    ]

    print("Select services to deploy (Enter = accept default):\n")
    selected = []
    for key, desc, default in available:
        default_str = "Y/n" if default else "y/N"
        choice = input(f"  [{default_str}] {desc}: ").strip().lower()
        if choice == "" and default:
            selected.append(key)
        elif choice in ("y", "yes"):
            selected.append(key)

    # Supabase
    print("")
    supa = input("  [y/N] Supabase    — Database/Auth platform: ").strip().lower()
    include_supabase = supa in ("y", "yes")

    # Network mode
    print("\nNetwork mode:")
    print("  1) Private (localhost only) [default]")
    print("  2) Public (LAN accessible)")
    env_choice = input("  Choice [1]: ").strip()
    environment = "public" if env_choice == "2" else "private"

    # Proxy
    proxy = "none"
    if environment == "public":
        print("\nReverse proxy:")
        if detect_swag():
            print("  SWAG detected on this system!")
            print("  1) Use SWAG (auto-configure)")
            print("  2) Use Caddy (built-in)")
            print("  3) None")
            proxy_choice = input("  Choice [1]: ").strip()
            if proxy_choice == "2":
                proxy = "caddy"
            elif proxy_choice == "3":
                proxy = "none"
            else:
                proxy = "swag"
        else:
            print("  1) Use Caddy (built-in) [default]")
            print("  2) None")
            proxy_choice = input("  Choice [1]: ").strip()
            proxy = "none" if proxy_choice == "2" else "caddy"

    print("\n" + "=" * 48)
    print("  Setup Summary")
    print("=" * 48)
    print(f"  Profile:    {detected_profile}")
    print(f"  Services:   {', '.join(selected)}")
    print(f"  Supabase:   {'Yes' if include_supabase else 'No'}")
    print(f"  Network:    {environment}")
    print(f"  Proxy:      {proxy}")
    print("=" * 48)

    return {
        "profile": detected_profile,
        "environment": environment,
        "services": selected,
        "no_supabase": not include_supabase,
        "no_caddy": proxy != "caddy",
        "proxy": proxy,
    }


# ---------------------- MAIN ---------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Deploy the Local AI Packaged stack with flexible service selection.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--profile", choices=["cpu", "gpu-nvidia", "gpu-amd", "none"], default="cpu",
                        help="Docker Compose profile for hardware target.")
    parser.add_argument("--environment", choices=["private", "public"], default="private",
                        help="Deployment network mode.")
    parser.add_argument("--services", nargs="+", default=["all"],
                        choices=["all"] + ALL_SELECTABLE,
                        help="Select which services to deploy.")
    parser.add_argument("--no-supabase", action="store_true", help="Skip Supabase.")
    parser.add_argument("--no-caddy", action="store_true", help="Skip Caddy reverse proxy.")
    parser.add_argument("--proxy", choices=["caddy", "swag", "none", "auto"], default="auto",
                        help="Reverse proxy type. 'auto' detects SWAG, falls back to Caddy.")
    parser.add_argument("--swag-dir", default=None,
                        help="Path to SWAG proxy-confs directory (auto-detected if not set).")
    parser.add_argument("--dry-run", action="store_true", help="Preview configuration without executing.")
    parser.add_argument("--update", action="store_true", help="Pull latest container images before starting.")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup wizard.")
    parser.add_argument("?", nargs="?", help=argparse.SUPPRESS)

    if "?" in sys.argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Interactive setup overrides CLI flags
    if args.setup:
        config = interactive_setup()
        args.profile = config["profile"]
        args.environment = config["environment"]
        args.services = config["services"]
        args.no_supabase = config["no_supabase"]
        args.no_caddy = config["no_caddy"]
        args.proxy = config["proxy"]

    # Resolve proxy type
    if args.proxy == "auto":
        if args.no_caddy:
            args.proxy = "none"
        elif detect_swag():
            print("SWAG reverse proxy detected on this system.")
            args.proxy = "swag"
            args.no_caddy = True
        else:
            args.proxy = "caddy"

    if args.proxy == "swag":
        args.no_caddy = True
    elif args.proxy == "none":
        args.no_caddy = True

    # 1. Clone Supabase if needed
    if not args.no_supabase:
        if not os.path.exists("supabase/docker/docker-compose.yml"):
            print("Supabase stack not found locally. Cloning from GitHub...")
            clone_supabase_repo()
        else:
            print("Supabase stack already present.")
        prepare_supabase_env()

    # 2. Check .env
    env_exists = os.path.exists(".env")

    # Build service list display
    if "all" in args.services:
        services_display = "ALL (n8n, Flowise, OpenWebUI, Qdrant, Neo4j, Langfuse, SearXNG, Ollama)"
    else:
        services_display = ", ".join(args.services)

    print("\n" + "=" * 40)
    print("  DEPLOYMENT SUMMARY")
    print("=" * 40)
    print(f"  Profile:      {args.profile}")
    print(f"  Environment:  {args.environment}")
    print(f"  Services:     {services_display}")
    print(f"  Supabase:     {'Disabled' if args.no_supabase else 'Enabled'}")
    print(f"  Proxy:        {args.proxy}")
    print(f"  .env file:    {'Present' if env_exists else 'Missing'}")
    print(f"  Update:       {'Yes' if args.update else 'No'}")
    print("=" * 40)

    if args.dry_run:
        print("\nDry-run mode: No containers will be started.")
        if "all" not in args.services:
            resolved = resolve_services(args.services)
            print(f"Resolved compose services: {', '.join(resolved)}")
        sys.exit(0)

    if not env_exists:
        check_or_generate_env()

    # 3. Modify docker-compose.yml
    toggle_supabase_include(disable_supabase=args.no_supabase)
    toggle_caddy_service(disable_caddy=args.no_caddy)

    # 4. Confirm
    confirm("Proceed with deployment?")

    # 5. SearXNG secret
    if "all" in args.services or "searxng" in args.services:
        generate_searxng_secret_key()

    # 6. Stop existing containers
    stop_existing_containers(args.profile)

    # 7. Update images
    if args.update:
        print("\nPulling latest container images...")
        try:
            cmd = [
                "docker", "compose", "-p", "localai",
                "--profile", args.profile,
                "-f", "docker-compose.yml", "pull"
            ]
            run_command(cmd)
            print("All container images updated successfully.")
        except subprocess.CalledProcessError:
            print("Failed to pull one or more images, continuing with existing ones.")

    # 8. Start Supabase
    if not args.no_supabase:
        print("\nStarting Supabase stack first...")
        try:
            cmd = [
                "docker", "compose", "-p", "localai",
                "-f", "supabase/docker/docker-compose.yml", "up", "-d"
            ]
            run_command(cmd)
            print("Supabase started successfully.")
        except subprocess.CalledProcessError:
            print("Could not start Supabase stack, continuing with Local AI services only.")

        print("Waiting 10 seconds for Supabase to initialize...")
        time.sleep(10)

    # 9. Start Local AI stack
    try:
        start_local_ai(args.profile, args.environment, args.services, supabase_enabled=not args.no_supabase)
    except Exception as e:
        print(f"\nDeployment encountered an error: {e}")
        print("Check the deployment report above for details.")

    # 10. SWAG proxy configuration
    if args.proxy == "swag":
        print("\nConfiguring SWAG reverse proxy...")
        swag_dir = args.swag_dir or find_swag_proxy_dir()
        if swag_dir:
            install_swag_confs(swag_dir)
        else:
            print("Could not find SWAG proxy-confs directory.")
            print("Use --swag-dir to specify the path manually.")

    print("\nDeployment finished.")


if __name__ == "__main__":
    main()
