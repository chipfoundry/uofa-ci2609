#!/usr/bin/env python3
"""
TinyTapeout Project Process Script

This script automates the complete setup process for a TinyTapeout project:
1. Clone project and rename based on project type (wokwi or verilog)
2. Clone tt-support-tools repository
3. Create user configuration
4. Harden the project
5. Create TT submission
6. Copy hardened project files

Usage: python3 process_tt_project.py <github_url>
"""

import subprocess
import sys
import os
import csv
import argparse
import tempfile
import shutil
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


def find_python_executable():
    """
    Find a suitable Python executable (3.11+ required for tt-support-tools).
    Returns the path to python3.11+, python3.13, python3.12, or falls back to python3.
    """
    # Check for Python 3.11+ in common locations
    python_versions = ['python3.13', 'python3.12', 'python3.11']
    
    for py_version in python_versions:
        try:
            result = subprocess.run(
                [py_version, '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                # Extract version number
                match = re.search(r'(\d+)\.(\d+)', version_str)
                if match:
                    major, minor = int(match.group(1)), int(match.group(2))
                    if major == 3 and minor >= 11:
                        return py_version
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            continue
    
    # Fallback to python3, but warn if it's too old
    try:
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            match = re.search(r'(\d+)\.(\d+)', version_str)
            if match:
                major, minor = int(match.group(1)), int(match.group(2))
                if major == 3 and minor < 11:
                    print(f"⚠️  Warning: Python {major}.{minor} detected, but tt-support-tools requires Python 3.11+")
                    print(f"   This may cause errors. Consider installing Python 3.11+ or using: python3.11")
    except Exception:
        pass
    
    return 'python3'


# Detect Python executable at module load time
PYTHON_CMD = find_python_executable()


def play_sound(sound_type="success"):
    """Play a system sound notification."""
    try:
        if sound_type == "success":
            # Play success sound (system bell or beep)
            print("\a", end="", flush=True)  # ASCII bell character
            # Also try system beep command
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                          capture_output=True, timeout=2)
        elif sound_type == "error":
            # Play error sound
            print("\a", end="", flush=True)  # ASCII bell character
            # Also try system beep command
            subprocess.run(["afplay", "/System/Library/Sounds/Basso.aiff"], 
                          capture_output=True, timeout=2)
    except Exception:
        # Fallback to simple beep if system sounds fail
        print("\a", end="", flush=True)


def run_command(command, description, capture_output=True, venv_bin_path=None):
    """Run a shell command and handle errors.
    
    Args:
        command: The command to run
        description: Description of the step
        capture_output: Whether to capture output
        venv_bin_path: Path to venv's bin directory (will be added to PATH)
    """
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    # Prepare environment with venv bin in PATH if provided
    env = None
    if venv_bin_path:
        env = os.environ.copy()
        current_path = env.get('PATH', '')
        env['PATH'] = f"{venv_bin_path}:{current_path}"
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=capture_output, text=True, env=env)
        print("✅ Success!")
        if result.stdout:
            print("Output:", result.stdout)
        return True, result.stdout if capture_output else ""
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        return False, e.stdout if capture_output else ""


def update_project_manifest(project_name, github_url, project_dir, manifest_dir=None):
    """Update the project manifest with new project information."""
    if manifest_dir is None:
        manifest_dir = os.getcwd()
    
    manifest_file = os.path.join(manifest_dir, "project_manifest.csv")
    
    # Define CSV headers
    headers = ["project_name", "github_url", "project_directory", "processed_date", "status"]
    
    # Load existing projects
    existing_projects = []
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                existing_projects = list(reader)
        except Exception as e:
            print(f"Warning: Could not read existing manifest: {e}")
            existing_projects = []
    
    # Create new project entry
    new_entry = {
        "project_name": project_name,
        "github_url": github_url,
        "project_directory": project_dir,
        "processed_date": datetime.now().isoformat(),
        "status": "completed"
    }
    
    # Check if project already exists (by github_url)
    existing_index = None
    for i, project in enumerate(existing_projects):
        if project["github_url"] == github_url:
            existing_index = i
            break
    
    if existing_index is not None:
        # Update existing entry
        existing_projects[existing_index] = new_entry
        print(f"✅ Updated existing project entry for {project_name}")
    else:
        # Add new entry
        existing_projects.append(new_entry)
        print(f"✅ Added new project entry for {project_name}")
    
    # Save manifest
    try:
        with open(manifest_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(existing_projects)
        print(f"✅ Project manifest updated: {manifest_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to update project manifest: {e}")
        return False


def check_project_exists(project_name, projects_dir):
    """Check if a project already exists in the projects directory."""
    project_path = os.path.join(projects_dir, project_name)
    return os.path.exists(project_path) and os.path.isdir(project_path)


def check_existing_gds_files(project_dir):
    """
    Check if the project already has GDS files from a previous build.
    Returns True if tt_submission directory exists with GDS files.
    """
    tt_submission_dir = os.path.join(project_dir, "tt_submission")
    if not os.path.exists(tt_submission_dir):
        return False
    
    # Check for GDS files in tt_submission
    import glob
    gds_files = glob.glob(os.path.join(tt_submission_dir, "*.gds"))
    return len(gds_files) > 0


def process_single_project(github_url, original_dir, temp_base_dir, skip_existing=False, use_existing_gds=False):
    """
    Process a single project from a GitHub URL.
    Returns (success: bool, error_type: str, error_message: str, project_name: str or None)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {github_url}")
    print(f"{'='*60}")
    
    # Validate URL first
    is_valid, error_type, error_message = validate_github_url(github_url)
    if not is_valid:
        return False, error_type, error_message, None
    
    # Check repository accessibility
    is_accessible, access_error_type, access_error_message = check_repository_accessibility(github_url)
    if not is_accessible:
        return False, access_error_type, access_error_message, None
    
    # Get the script directory to find get_project.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    get_project_script = os.path.join(script_dir, "get_project.py")
    
    # Change to temp directory for cloning
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_base_dir)
    except Exception as e:
        print(f"❌ Failed to change to temp directory: {e}")
        return False, "internal_error", f"Failed to change to temp directory: {e}", None
    
    # Step 1: Clone project and rename based on project type
    success, output = run_command(
        f"{PYTHON_CMD} {get_project_script} {github_url}",
        "Clone project and rename based on project type (wokwi or verilog)"
    )
    
    if not success:
        print(f"❌ Failed to clone and rename project: {github_url}")
        os.chdir(original_cwd)
        # Try to determine error type from output
        error_output = output.lower() if output else ""
        if 'not found' in error_output or 'does not exist' in error_output:
            return False, "not_found", "Repository not found during clone", None
        elif 'permission denied' in error_output or 'authentication' in error_output:
            return False, "private", "Repository is private or requires authentication", None
        else:
            return False, "clone_error", "Failed to clone repository", None
    
    # Parse the directory name from the output
    project_dir = None
    for line in output.split('\n'):
        if "Success! Project cloned and renamed to:" in line:
            # Extract directory name from the line
            project_dir = line.split(":")[-1].strip()
            break
    
    if not project_dir:
        print(f"❌ Could not parse project directory from get_project.py output: {github_url}")
        os.chdir(original_cwd)
        return False, "parse_error", "Could not parse project directory from output", None
    
    # Check if project already exists (if skip_existing is enabled)
    if skip_existing:
        projects_dir = os.path.join(original_dir, "projects")
        if check_project_exists(project_dir, projects_dir):
            print(f"⏭️  Skipping {project_dir} - already exists in projects directory")
            os.chdir(original_cwd)
            return True, "skipped", f"Project {project_dir} already exists", project_dir
    
    # Get full path to project directory
    project_full_path = os.path.join(temp_base_dir, project_dir)
    
    print(f"\n{'='*60}")
    print(f"Step: Change to project directory")
    print(f"Directory: {project_full_path}")
    print(f"{'='*60}")
    
    try:
        os.chdir(project_full_path)
        print(f"✅ Successfully changed to: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Failed to change directory: {e}")
        os.chdir(original_cwd)
        return False, "internal_error", f"Failed to change directory: {e}", None
    
    # Step 2: Clone tt-support-tools repository
    success, _ = run_command(
        "git clone https://github.com/TinyTapeout/tt-support-tools.git tt",
        "Clone tt-support-tools repository"
    )
    if not success:
        print(f"❌ Failed to clone repository for: {github_url}")
        os.chdir(original_dir)
        return False, "tt_tools_error", "Failed to clone tt-support-tools", None
    
    # Step 2.5: Use shared virtual environment at repository root to avoid externally-managed-environment issues
    # Check if venv exists at repository root, create if it doesn't
    venv_path = os.path.join(original_dir, ".venv")
    if not os.path.exists(venv_path):
        print(f"📦 Creating shared virtual environment at: {venv_path}")
        success, _ = run_command(
            f"{PYTHON_CMD} -m venv {venv_path}",
            "Create shared virtual environment"
        )
        if not success:
            print(f"❌ Failed to create virtual environment")
            os.chdir(original_dir)
            return False, "venv_error", "Failed to create virtual environment", None
    else:
        print(f"📦 Using existing shared virtual environment at: {venv_path}")
    
    # Determine the Python executable in the venv (works on both Unix and Windows)
    if sys.platform == "win32":
        venv_bin_path = os.path.join(venv_path, "Scripts")
        venv_python = os.path.join(venv_bin_path, "python.exe")
        venv_pip = os.path.join(venv_bin_path, "pip.exe")
    else:
        venv_bin_path = os.path.join(venv_path, "bin")
        venv_python = os.path.join(venv_bin_path, "python")
        venv_pip = os.path.join(venv_bin_path, "pip")
    
    # Step 2.6: Install Python dependencies for tt-support-tools in venv
    # First try installing requirements.txt, but if it fails due to version conflicts,
    # try installing critical packages individually
    success, output = run_command(
        f"{venv_pip} install -r tt/requirements.txt",
        "Install Python dependencies for tt-support-tools",
        venv_bin_path=venv_bin_path
    )
    
    # Install librelane separately (not in requirements.txt but required for hardening)
    if success:
        librelane_success, _ = run_command(
            f"{venv_pip} install 'librelane>=2.4.0'",
            "Install librelane package (required for hardening)",
            venv_bin_path=venv_bin_path,
            capture_output=True
        )
        if not librelane_success:
            print(f"   ⚠️  Warning: Failed to install librelane, hardening may fail")
    if not success:
        print(f"⚠️  Warning: Failed to install all dependencies from requirements.txt")
        print(f"   Attempting to install critical packages individually...")
        
        # Install critical packages that are most likely needed
        # Note: Some packages like klayout might require special installation
        critical_packages = [
            "chevron", 
            "pyyaml", 
            "click",
            "numpy",
            "requests",
            "gitpython",
            "gdstk",
            "cairosvg",
            "mistune",
            "python-frontmatter",
            "brotli"
        ]
        
        # Try to install klayout separately as it might need special handling
        klayout_installed = False
        klayout_success, _ = run_command(
            f"{venv_pip} install 'klayout>=0.29.0,<0.30.0'",
            "Install klayout package",
            venv_bin_path=venv_bin_path,
            capture_output=True
        )
        if klayout_success:
            klayout_installed = True
        else:
            print(f"   ⚠️  Failed to install klayout via pip (may require system installation)")
            print(f"   Note: klayout might need to be installed separately or via conda")
        
        for package in critical_packages:
            install_success, _ = run_command(
                f"{venv_pip} install {package}",
                f"Install {package} package",
                venv_bin_path=venv_bin_path,
                capture_output=True
            )
            if not install_success:
                print(f"   ⚠️  Failed to install {package}, but continuing...")
        
        # Install librelane (required for hardening, not in requirements.txt)
        librelane_success, _ = run_command(
            f"{venv_pip} install 'librelane>=2.4.0'",
            "Install librelane package (required for hardening)",
            venv_bin_path=venv_bin_path,
            capture_output=True
        )
        if not librelane_success:
            print(f"   ⚠️  Warning: Failed to install librelane, hardening may fail")
        
        # Check if critical packages are available
        critical_checks = [
            ("chevron", "chevron"),
            ("yaml", "pyyaml"),
        ]
        
        missing_critical = []
        for module_name, package_name in critical_checks:
            check_success, _ = run_command(
                f"{venv_python} -c 'import {module_name}; print(\"{module_name} available\")'",
                f"Verify {package_name} is installed",
                capture_output=True
            )
            if not check_success:
                missing_critical.append(package_name)
        
        if missing_critical:
            print(f"❌ Critical dependencies are still not available: {', '.join(missing_critical)}")
            print(f"   You may need to install dependencies manually:")
            print(f"   {venv_pip} install {' '.join(missing_critical)}")
            os.chdir(original_dir)
            return False, "dependency_error", f"Failed to install required dependencies ({', '.join(missing_critical)})", None
        
        # Warn about klayout if it's not installed but don't fail
        if not klayout_installed:
            klayout_check, _ = run_command(
                f"{venv_python} -c 'import klayout.db; print(\"klayout available\")'",
                "Verify klayout is installed",
                capture_output=True
            )
            if not klayout_check:
                print(f"⚠️  Warning: klayout is not available")
                print(f"   This may cause errors later. You may need to install it:")
                print(f"   {venv_pip} install klayout  (or install via conda/system package manager)")
    
    # Step 3: Create user configuration
    success, _ = run_command(
        f"{venv_python} tt/tt_tool.py --create-user-config",
        "Create user configuration",
        venv_bin_path=venv_bin_path
    )
    if not success:
        print(f"❌ Failed to create user configuration for: {github_url}")
        os.chdir(original_dir)
        return False, "config_error", "Failed to create user configuration", None
    
    # Step 4: Harden the project (or use existing GDS files)
    has_existing_gds = use_existing_gds and check_existing_gds_files(project_full_path)
    if has_existing_gds:
        print(f"📦 Using existing GDS files from tt_submission directory")
        print(f"   Skipping hardening step (--use-existing-gds enabled)")
        # Still need to create tt_submission if it doesn't have all required files
        # But check if it's already complete
        import glob
        tt_submission_dir = os.path.join(project_full_path, "tt_submission")
        has_gds = len(glob.glob(os.path.join(tt_submission_dir, "*.gds"))) > 0
        has_lef = len(glob.glob(os.path.join(tt_submission_dir, "*.lef"))) > 0
        has_commit_id = os.path.exists(os.path.join(tt_submission_dir, "commit_id.json"))
        
        if has_gds and has_lef and has_commit_id:
            print(f"   tt_submission appears complete, skipping create-tt-submission")
            skip_submission = True
        else:
            print(f"   tt_submission incomplete, will run create-tt-submission")
            skip_submission = False
    else:
        if use_existing_gds:
            print(f"⚠️  No existing GDS files found, will rebuild")
        skip_submission = False
    
    if not has_existing_gds:
        success, _ = run_command(
            f"{venv_python} tt/tt_tool.py --harden",
            "Harden the project",
            venv_bin_path=venv_bin_path
        )
        if not success:
            print(f"❌ Failed to harden project: {github_url}")
            os.chdir(original_dir)
            return False, "harden_error", "Failed to harden project", None
    
    # Step 5: Create TT submission (if needed)
    if not skip_submission:
        success, _ = run_command(
            f"{venv_python} tt/tt_tool.py --create-tt-submission",
            "Create TT submission",
            venv_bin_path=venv_bin_path
        )
        if not success:
            print(f"❌ Failed to create TT submission for: {github_url}")
            os.chdir(original_dir)
            return False, "submission_error", "Failed to create TT submission", None
    
    # Step 6: Copy hardened project
    # Get the script directory to find copy_hardened_project.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    copy_script = os.path.join(script_dir, "copy_hardened_project.py")
    
    # Get projects directory (relative to original_dir)
    projects_dir = os.path.join(original_dir, "projects")
    
    success, _ = run_command(
        f"{PYTHON_CMD} {copy_script} -s . -p {projects_dir}",
        "Copy hardened project files"
    )
    if not success:
        print(f"❌ Failed to copy hardened project: {github_url}")
        os.chdir(original_dir)
        return False, "copy_error", "Failed to copy hardened project", None
    
    # Step 7: Update project manifest
    # Get the current directory name (should be the project directory)
    current_dir = os.path.basename(os.getcwd())
    project_name = current_dir
    
    print(f"\n{'='*60}")
    print(f"Step: Update project manifest")
    print(f"Project: {project_name}")
    print(f"GitHub URL: {github_url}")
    print(f"Manifest location: {original_dir}")
    print(f"{'='*60}")
    
    if not update_project_manifest(project_name, github_url, current_dir, original_dir):
        print(f"⚠️  Failed to update project manifest for: {github_url}")
    
    # Return to original directory
    os.chdir(original_dir)
    return True, None, None, project_dir


def validate_github_url(url):
    """
    Validate if a URL is a valid GitHub repository URL.
    Returns (is_valid, error_type, error_message)
    """
    if not url or not url.strip():
        return False, "empty", "Empty URL"
    
    url = url.strip()
    
    # Check if it's a Wokwi URL
    if 'wokwi.com' in url.lower():
        return False, "wokwi", "Wokwi project URL (not a GitHub repository)"
    
    # Check if it's a GDS viewer URL
    if 'gds-viewer.tinytapeout.com' in url.lower():
        return False, "gds_viewer", "GDS viewer URL (not a GitHub repository)"
    
    # Check if it's a GitHub URL
    if 'github.com' not in url.lower():
        return False, "not_github", "Not a GitHub URL"
    
    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, "malformed", f"Malformed URL: {e}"
    
    # Check if it has a valid GitHub domain
    if 'github.com' not in parsed.netloc.lower():
        return False, "not_github", "Not a GitHub URL"
    
    # Check for invalid GitHub URL patterns
    if '/tree/' in url or '/blob/' in url or '/actions' in url or '/issues' in url:
        return False, "invalid_path", "GitHub URL contains invalid path (use base repository URL, e.g., https://github.com/user/repo.git)"
    
    # Check if it looks like a valid repository path
    path_parts = [p for p in parsed.path.split('/') if p]
    if len(path_parts) < 2:
        return False, "invalid_path", "GitHub URL missing user/repository path"
    
    # If it doesn't end with .git, that's okay, but warn
    # Actually, let's accept both .git and non-.git URLs
    
    return True, None, None


def check_repository_accessibility(url):
    """
    Check if a GitHub repository is accessible (not private or not found).
    Returns (is_accessible, error_type, error_message)
    """
    # Try to clone with --depth 1 to check accessibility
    # Use a very short timeout to avoid hanging
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, None, None
        else:
            error_output = result.stderr.lower()
            if 'not found' in error_output or 'does not exist' in error_output:
                return False, "not_found", "Repository not found (may be private or deleted)"
            elif 'permission denied' in error_output or 'authentication' in error_output:
                return False, "private", "Repository is private or requires authentication"
            else:
                return False, "access_error", f"Repository access error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "timeout", "Repository check timed out (may be private or network issue)"
    except Exception as e:
        return False, "check_error", f"Error checking repository: {str(e)}"


def load_urls_from_file(file_path):
    """Load GitHub URLs from a file (one URL per line)."""
    urls = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append((line, line_num))
        return urls
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return []


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Process TinyTapeout project(s) from GitHub URL(s)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single project
  python3 process_tt_project.py https://github.com/user/project.git
  
  # Process multiple projects from command line
  python3 process_tt_project.py https://github.com/user/proj1.git https://github.com/user/proj2.git
  
  # Process projects from a file (one URL per line)
  python3 process_tt_project.py --file projects.txt
  
  # Process only the first 5 projects
  python3 process_tt_project.py --file projects.txt --limit 5
  
  # Skip projects that already exist
  python3 process_tt_project.py --file projects.txt --skip-existing
  
  # Use existing GDS files from GitHub Actions (skip rebuilding)
  python3 process_tt_project.py --file projects.txt --use-existing-gds
        """
    )
    parser.add_argument('github_urls', nargs='*', help='GitHub repository URL(s) to clone and process')
    parser.add_argument('--file', '-f', help='File containing GitHub URLs (one per line)')
    parser.add_argument('--limit', '-n', type=int, help='Process only the first N projects')
    parser.add_argument('--skip-existing', action='store_true', help='Skip projects that already exist in the projects directory')
    parser.add_argument('--use-existing-gds', action='store_true', help='Use existing GDS files from tt_submission if available (skip hardening)')
    parser.add_argument('--help-steps', action='store_true', help='Show detailed step information')
    
    args = parser.parse_args()
    
    # Show detailed steps if requested
    if args.help_steps:
        print("📋 TinyTapeout Project Processing Steps:")
        print("1. Clone project and rename based on project type (wokwi or verilog)")
        print("2. Clone tt-support-tools repository")
        print("3. Create user configuration")
        print("4. Harden the project")
        print("5. Create TT submission")
        print("6. Copy hardened project files")
        print("7. Update project manifest")
        print("8. Change to project directory")
        print("\nUsage:")
        print("  python3 process_tt_project.py <github_url>")
        print("  python3 process_tt_project.py <url1> <url2> ...")
        print("  python3 process_tt_project.py --file projects.txt")
        sys.exit(0)
    
    # Collect all URLs to process
    urls_to_process = []
    
    # Add URLs from file if provided
    if args.file:
        file_urls = load_urls_from_file(args.file)
        if file_urls:
            # Convert (url, line_num) tuples to just URLs for processing
            urls_to_process.extend([url for url, _ in file_urls])
            # Store line numbers for reporting
            url_line_map = {url: line_num for url, line_num in file_urls}
            print(f"📄 Loaded {len(file_urls)} URL(s) from {args.file}")
        else:
            print(f"❌ No valid URLs found in {args.file}")
            sys.exit(1)
    else:
        url_line_map = {}
    
    # Add URLs from command line arguments
    if args.github_urls:
        urls_to_process.extend(args.github_urls)
    
    # Validate we have at least one URL
    if not urls_to_process:
        parser.print_help()
        print("\n❌ Error: No GitHub URLs provided. Use --file or provide URLs as arguments.")
        sys.exit(1)
    
    # Apply limit if specified
    if args.limit and args.limit > 0:
        if args.limit < len(urls_to_process):
            print(f"📌 Limiting to first {args.limit} project(s) out of {len(urls_to_process)} total")
            urls_to_process = urls_to_process[:args.limit]
    
    original_dir = os.getcwd()  # Store the original directory for manifest updates
    
    print("🚀 Starting TinyTapeout Project Processing")
    print(f"Working directory: {original_dir}")
    print(f"Python executable: {PYTHON_CMD}")
    print(f"Total projects to process: {len(urls_to_process)}")
    
    # Create a temporary directory for cloning projects
    temp_base_dir = tempfile.mkdtemp(prefix="tt_projects_")
    print(f"📁 Using temporary directory: {temp_base_dir}")
    
    # Process each project
    successful = []
    failed = []
    skipped = []  # Projects that were skipped (already exist)
    invalid_urls = []  # URLs that are not valid GitHub URLs
    private_urls = []  # Private or not found repositories
    processing_errors = []  # Other processing errors
    
    try:
        for i, github_url in enumerate(urls_to_process, 1):
            print(f"\n{'#'*60}")
            print(f"Project {i}/{len(urls_to_process)}: {github_url}")
            print(f"{'#'*60}")
            
            success, error_type, error_message, project_name = process_single_project(
                github_url, original_dir, temp_base_dir, 
                skip_existing=args.skip_existing,
                use_existing_gds=args.use_existing_gds
            )
            
            if success:
                if error_type == "skipped":
                    skipped.append((github_url, project_name))
                    print(f"⏭️  Skipped (already exists): {github_url}")
                else:
                    successful.append(github_url)
                    print(f"✅ Successfully processed: {github_url}")
            else:
                failed.append(github_url)
                print(f"❌ Failed to process: {github_url}")
            
                # Categorize the error
                if error_type in ["wokwi", "gds_viewer", "not_github", "malformed", "invalid_path"]:
                    invalid_urls.append((github_url, error_type, error_message))
                elif error_type in ["private", "not_found", "access_error", "timeout"]:
                    private_urls.append((github_url, error_type, error_message))
                else:
                    processing_errors.append((github_url, error_type, error_message))
    
    finally:
        # Clean up temporary directory
        print(f"\n{'='*60}")
        print(f"Cleaning up temporary directory: {temp_base_dir}")
        print(f"{'='*60}")
        try:
            shutil.rmtree(temp_base_dir)
            print(f"✅ Temporary directory cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up temporary directory: {e}")
            print(f"   You may need to manually remove: {temp_base_dir}")
    
    # Generate detailed report (both to console and file)
    report_lines = []
    
    def add_report_line(line=""):
        """Add a line to both console output and report file."""
        print(line)
        report_lines.append(line)
    
    add_report_line(f"\n{'='*60}")
    add_report_line("📊 Processing Summary")
    add_report_line(f"{'='*60}")
    add_report_line(f"Total projects: {len(urls_to_process)}")
    add_report_line(f"✅ Successful: {len(successful)}")
    if skipped:
        add_report_line(f"⏭️  Skipped: {len(skipped)}")
    add_report_line(f"❌ Failed: {len(failed)}")
    
    if successful:
        add_report_line(f"\n✅ Successfully processed projects ({len(successful)}):")
        for url in successful:
            line_info = f" (line {url_line_map.get(url, 'N/A')})" if url_line_map else ""
            add_report_line(f"   - {url}{line_info}")
    
    if skipped:
        add_report_line(f"\n⏭️  Skipped projects ({len(skipped)}):")
        for url, project_name in skipped:
            line_info = f" (line {url_line_map.get(url, 'N/A')})" if url_line_map else ""
            add_report_line(f"   - {url}{line_info} -> {project_name}")
    
    # Detailed failure report
    add_report_line(f"\n{'='*60}")
    add_report_line("📋 Detailed Failure Report")
    add_report_line(f"{'='*60}")
    
    if invalid_urls:
        add_report_line(f"\n❌ Invalid URLs ({len(invalid_urls)}):")
        add_report_line("   These URLs are not valid GitHub repository URLs:")
        for url, error_type, error_message in invalid_urls:
            line_info = f" (line {url_line_map.get(url, 'N/A')})" if url_line_map else ""
            add_report_line(f"   - {url}{line_info}")
            add_report_line(f"     Error: {error_message}")
    
    if private_urls:
        add_report_line(f"\n🔒 Private or Inaccessible Repositories ({len(private_urls)}):")
        add_report_line("   These repositories are private, not found, or inaccessible:")
        for url, error_type, error_message in private_urls:
            line_info = f" (line {url_line_map.get(url, 'N/A')})" if url_line_map else ""
            add_report_line(f"   - {url}{line_info}")
            add_report_line(f"     Error: {error_message}")
    
    if processing_errors:
        add_report_line(f"\n⚠️  Processing Errors ({len(processing_errors)}):")
        add_report_line("   These repositories had errors during processing:")
        for url, error_type, error_message in processing_errors:
            line_info = f" (line {url_line_map.get(url, 'N/A')})" if url_line_map else ""
            add_report_line(f"   - {url}{line_info}")
            add_report_line(f"     Error Type: {error_type}")
            add_report_line(f"     Message: {error_message}")
    
    # Summary statistics
    add_report_line(f"\n{'='*60}")
    add_report_line("📈 Summary Statistics")
    add_report_line(f"{'='*60}")
    add_report_line(f"Total URLs processed: {len(urls_to_process)}")
    add_report_line(f"✅ Successful: {len(successful)} ({len(successful)*100//len(urls_to_process) if urls_to_process else 0}%)")
    if skipped:
        add_report_line(f"⏭️  Skipped: {len(skipped)} ({len(skipped)*100//len(urls_to_process) if urls_to_process else 0}%)")
    add_report_line(f"❌ Invalid URLs: {len(invalid_urls)} ({len(invalid_urls)*100//len(urls_to_process) if urls_to_process else 0}%)")
    add_report_line(f"🔒 Private/Inaccessible: {len(private_urls)} ({len(private_urls)*100//len(urls_to_process) if urls_to_process else 0}%)")
    add_report_line(f"⚠️  Processing Errors: {len(processing_errors)} ({len(processing_errors)*100//len(urls_to_process) if urls_to_process else 0}%)")
    
    # Note about overwriting
    if not args.skip_existing:
        add_report_line(f"\nℹ️  Note: Projects are overwritten by default. Use --skip-existing to skip existing projects.")
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = os.path.join(original_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_filename = f"processing_report_{timestamp}.txt"
    report_filepath = os.path.join(reports_dir, report_filename)
    
    try:
        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("TinyTapeout Project Processing Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Working Directory: {original_dir}\n")
            if args.file:
                f.write(f"Input File: {args.file}\n")
            f.write("\n")
            f.write("\n".join(report_lines))
            f.write("\n")
        
        print(f"\n{'='*60}")
        print(f"📄 Report saved to: {report_filepath}")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n⚠️  Warning: Failed to save report to file: {e}")
    
    if failed:
        play_sound("error")
        sys.exit(1)
    else:
        print("\n🎉 All projects processed successfully!")
        play_sound("success")


if __name__ == "__main__":
    main()
