"""
Development helper script.
Quick commands for common development tasks.
"""

import os
import sys
import subprocess
import argparse


def run_command(cmd, cwd=None):
    """Run a shell command."""
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode == 0


def test():
    """Run installation tests."""
    print("Running installation tests...")
    return run_command("python test_installation.py")


def run_local():
    """Run bot locally (without Docker)."""
    print("Starting PromoBot locally...")
    return run_command("python src/main.py")


def docker_build():
    """Build Docker image."""
    print("Building Docker image...")
    return run_command("docker-compose build")


def docker_up():
    """Start Docker container."""
    print("Starting Docker container...")
    return run_command("docker-compose up")


def docker_up_detached():
    """Start Docker container in background."""
    print("Starting Docker container in background...")
    return run_command("docker-compose up -d")


def docker_down():
    """Stop Docker container."""
    print("Stopping Docker container...")
    return run_command("docker-compose down")


def docker_logs():
    """Show Docker logs."""
    print("Showing Docker logs...")
    return run_command("docker-compose logs -f")


def clean_data():
    """Clean database and cookies."""
    print("Cleaning data...")
    if os.path.exists("data/deals.db"):
        os.remove("data/deals.db")
        print("✓ Removed deals.db")
    if os.path.exists("data/cookies.pkl"):
        os.remove("data/cookies.pkl")
        print("✓ Removed cookies.pkl")
    print("Data cleaned!")
    return True


def clean_logs():
    """Clean log files."""
    print("Cleaning logs...")
    if os.path.exists("logs"):
        import shutil
        shutil.rmtree("logs")
        print("✓ Removed logs directory")
    print("Logs cleaned!")
    return True


def install_deps():
    """Install Python dependencies."""
    print("Installing dependencies...")
    return run_command("pip install -r requirements.txt")


def main():
    parser = argparse.ArgumentParser(description="PromoBot Development Helper")
    parser.add_argument(
        "command",
        choices=[
            "test",
            "run",
            "build",
            "up",
            "up-d",
            "down",
            "logs",
            "clean-data",
            "clean-logs",
            "install"
        ],
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    commands = {
        "test": test,
        "run": run_local,
        "build": docker_build,
        "up": docker_up,
        "up-d": docker_up_detached,
        "down": docker_down,
        "logs": docker_logs,
        "clean-data": clean_data,
        "clean-logs": clean_logs,
        "install": install_deps,
    }
    
    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
