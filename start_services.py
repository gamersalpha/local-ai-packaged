#!/usr/bin/env python3
"""
start_services.py
Version complète et stable :
- Gère automatiquement Supabase et Caddy dans docker-compose.yml
- Vérifie / génère le .env si manquant
- Récapitulatif clair avant déploiement
- Confirmation utilisateur
- Options : --no-supabase, --no-caddy, --update, --dry-run
"""

import os
import subprocess
import shutil
import time
import argparse
import sys


# ---------------------- UTILS ---------------------- #

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def confirm(prompt):
    """Ask the user to confirm with OK or cancel."""
    while True:
        choice = input(f"\n{prompt} (OK / cancel): ").strip().lower()
        if choice in ["ok", "o"]:
            return True
        elif choice in ["cancel", "c", "n"]:
            print("❌ Operation cancelled.")
            sys.exit(0)
        else:
            print("Please type OK or cancel.")


# ---------------------- ENV MANAGEMENT ---------------------- #

def check_or_generate_env():
    """Check if .env exists. If not, offer to generate it."""
    env_path = ".env"
    if os.path.exists(env_path):
        print("✅ .env file detected.")
        return True
    else:
        print("⚠️  No .env file detected!")
        print("Without it, Docker will raise many missing variable warnings.")
        choice = input("\nDo you want to generate one now using generate_env.py? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            if not os.path.exists("generate_env.py"):
                print("❌ generate_env.py not found in current directory.")
                sys.exit(1)
            print("🧩 Generating .env file with sensitive values...")
            run_command(["python3", "generate_env.py", "--yes", "--regen-sensitive"])
            print("✅ .env generated successfully.")
            return True
        else:
            print("❌ Aborting. You must have a valid .env file to continue.")
            sys.exit(1)


# ---------------------- YAML MODIFIERS ---------------------- #

def toggle_supabase_include(disable_supabase: bool):
    """(Dé)commente la ligne include: ./supabase/docker/docker-compose.yml."""
    compose_path = "docker-compose.yml"
    if not os.path.exists(compose_path):
        print("⚠️  docker-compose.yml not found, skipping Supabase include management.")
        return

    with open(compose_path, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if not disable_supabase and stripped.startswith("#") and "supabase/docker/docker-compose.yml" in stripped:
            new_lines.append(line.replace("#", "", 1))
            modified = True
        elif disable_supabase and not stripped.startswith("#") and "supabase/docker/docker-compose.yml" in stripped:
            new_lines.append("# " + line)
            modified = True
        else:
            new_lines.append(line)

    if modified:
        with open(compose_path, "w") as f:
            f.writelines(new_lines)
        state = "commented out" if disable_supabase else "restored"
        print(f"🔧 Supabase include line automatically {state} in docker-compose.yml.")


def toggle_caddy_service(disable_caddy: bool):
    """(Dé)commente le bloc du service 'caddy:'."""
    compose_path = "docker-compose.yml"
    if not os.path.exists(compose_path):
        print("⚠️  docker-compose.yml not found, skipping Caddy management.")
        return

    with open(compose_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    modified = False
    in_caddy_block = False

    for line in lines:
        stripped = line.strip()

        # Début du bloc caddy
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

        # Fin du bloc caddy
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

        # Ligne normale
        new_lines.append(line)

    if modified:
        with open(compose_path, "w") as f:
            f.writelines(new_lines)
        state = "commented out" if disable_caddy else "restored"
        print(f"🔧 Caddy service automatically {state} in docker-compose.yml.")


# ---------------------- SEARXNG ---------------------- #

def generate_searxng_secret_key():
    """Generate a secret key for SearXNG."""
    settings_path = os.path.join("searxng", "settings.yml")
    base_path = os.path.join("searxng", "settings-base.yml")

    if not os.path.exists(base_path):
        print("⚠️ Base settings not found, skipping SearXNG key generation.")
        return

    if not os.path.exists(settings_path):
        print("📝 Creating settings.yml from base...")
        shutil.copyfile(base_path, settings_path)

    print("🔑 Generating SearXNG secret key...")
    try:
        random_key = subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode().strip()
        sed_cmd = ["sed", "-i", f"s|ultrasecretkey|{random_key}|g", settings_path]
        subprocess.run(sed_cmd, check=True)
        print("✅ SearXNG secret key generated.")
    except Exception as e:
        print(f"❌ Error generating key: {e}")


# ---------------------- DOCKER ACTIONS ---------------------- #

def stop_existing_containers(profile=None):
    """Stop existing containers for the project."""
    print("🧹 Stopping and removing existing containers for project 'localai'...")
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml", "down"])
    try:
        run_command(cmd)
    except subprocess.CalledProcessError:
        print("⚠️  Docker compose down returned a non-zero exit code. Continuing.")


def start_local_ai(profile=None, environment=None):
    """Start local AI stack."""
    print("🚀 Starting Local AI stack...")
    cmd = ["docker", "compose", "-p", "localai"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml"])
    if environment == "private":
        cmd.extend(["-f", "docker-compose.override.private.yml"])
    elif environment == "public":
        cmd.extend(["-f", "docker-compose.override.public.yml"])
    cmd.extend(["up", "-d"])
    run_command(cmd)

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
        print("📄 Copying root .env → supabase/docker/.env ...")
        shutil.copyfile(src, dst)
    else:
        print("⚠️ No .env found at root. Supabase will fail without it.")

# ---------------------- MAIN ---------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Start, update, or preview the Supabase + Local AI stack.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--profile", choices=["cpu", "gpu-nvidia", "gpu-amd", "none"], default="cpu",
                        help="Docker Compose profile to use (hardware target).")
    parser.add_argument("--environment", choices=["private", "public"], default="private",
                        help="Deployment environment mode.")
    parser.add_argument("--no-supabase", action="store_true", help="Skip Supabase (comment include line).")
    parser.add_argument("--no-caddy", action="store_true", help="Skip Caddy (comment service block).")
    parser.add_argument("--dry-run", action="store_true", help="Preview configuration without executing.")
    parser.add_argument("--update", action="store_true", help="Pull the latest container images before starting.")
    parser.add_argument("?", nargs="?", help=argparse.SUPPRESS)

    if "?" in sys.argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # 🪄 1️⃣ Cloner Supabase si besoin
    if not args.no_supabase:
        if not os.path.exists("supabase/docker/docker-compose.yml"):
            print("🧩 Supabase stack not found locally. Cloning it from GitHub...")
            clone_supabase_repo()
        else:
            print("✅ Supabase stack already present.")
        prepare_supabase_env()


    # 🧩 2️⃣ Vérifier le fichier .env
    env_exists = os.path.exists(".env")

    print("\n==============================")
    print("🧭  DEPLOYMENT SUMMARY")
    print("==============================")
    print(f"💻 Profile: {args.profile}")
    print(f"🌍 Environment: {args.environment}")
    print(f"🧩 Supabase: {'❌ Disabled' if args.no_supabase else '✅ Enabled'}")
    print(f"🪶 Caddy: {'❌ Disabled' if args.no_caddy else '✅ Enabled'}")
    print(f"📁 .env file: {'✅ Present' if env_exists else '❌ Missing'}")
    print(f"🔄 Update images: {'✅ Yes' if args.update else '❌ No'}")
    print(f"🧠 Services: n8n, Flowise, OpenWebUI, Qdrant, Neo4j, Langfuse, Redis, SearXNG, Ollama")
    print("==============================")

    if args.dry_run:
        print("\n🧪 Dry-run mode active: No containers will be started.")
        sys.exit(0)

    if not env_exists:
        check_or_generate_env()

    # 🧩 3️⃣ Modifier docker-compose.yml selon les options
    toggle_supabase_include(disable_supabase=args.no_supabase)
    toggle_caddy_service(disable_caddy=args.no_caddy)

    # 🧠 4️⃣ Confirmation avant lancement
    confirm("Proceed with deployment?")

    # 🔑 5️⃣ Génération clé SearXNG
    generate_searxng_secret_key()

    # 🧹 6️⃣ Stopper les conteneurs existants
    stop_existing_containers(args.profile)

    # ⬇️ 7️⃣ Option : mise à jour des images
    if args.update:
        print("⬇️ Pulling latest container images...")
        try:
            cmd = [
                "docker", "compose", "-p", "localai",
                "--profile", args.profile,
                "-f", "docker-compose.yml", "pull"
            ]
            run_command(cmd)
            print("✅ All container images updated successfully.")
        except subprocess.CalledProcessError:
            print("⚠️  Failed to pull one or more images, continuing with existing ones.")

    # 🚀 8️⃣ Démarrage des stacks
    if not args.no_supabase:
        print("\n🧱 Starting Supabase stack first...")
        try:
            cmd = [
                "docker", "compose", "-p", "localai",
                "-f", "supabase/docker/docker-compose.yml", "up", "-d"
            ]
            run_command(cmd)
            print("✅ Supabase started successfully.")
        except subprocess.CalledProcessError:
            print("⚠️  Could not start Supabase stack, continuing with Local AI services only.")

        print("⏳ Waiting 10 seconds for Supabase to initialize...")
        time.sleep(10)

    # 🚀 9️⃣ Démarrage du stack Local AI
    start_local_ai(args.profile, args.environment)

    print("\n✅ Deployment complete!")


if __name__ == "__main__":
    main()
