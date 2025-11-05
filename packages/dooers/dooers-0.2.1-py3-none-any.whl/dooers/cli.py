import io
import os
import tarfile
import tempfile
import json
import base64
import time
import warnings
from pathlib import Path
import threading
import itertools
import sys
import fnmatch

import requests
import typer
from tqdm import tqdm

# Suppress urllib3 SSL warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

app = typer.Typer(add_completion=False, help="Dooers CLI")

# Global auth state
AUTH_TOKEN = None

# Token storage file
TOKEN_FILE = Path.home() / ".dooers_token"

def _load_token():
    """Load token from file"""
    global AUTH_TOKEN
    if TOKEN_FILE.exists():
        try:
            AUTH_TOKEN = TOKEN_FILE.read_text().strip()
        except Exception as e:
            AUTH_TOKEN = None
    else:
        AUTH_TOKEN = None
    return AUTH_TOKEN

def _save_token(token):
    """Save token to file with secure permissions"""
    global AUTH_TOKEN
    AUTH_TOKEN = token
    try:
        TOKEN_FILE.write_text(token)
        # Set secure file permissions (owner read/write only)
        TOKEN_FILE.chmod(0o600)
    except Exception:
        pass

def _clear_token():
    """Clear token from memory and file"""
    global AUTH_TOKEN
    AUTH_TOKEN = None
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception:
        pass


def _is_token_expired(token):
    """Check if JWT token is expired"""
    try:
        # JWT tokens have 3 parts, JWE tokens have 5 parts, but this one has 4 parts
        parts = token.split('.')
        if len(parts) not in [3, 4, 5]:
            return True
        
        # For JWT (3 parts): payload is parts[1]
        # For JWE (4-5 parts): payload is parts[1] 
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        
        # Check expiration
        exp = data.get('exp', 0)
        current_time = int(time.time())
        is_expired = current_time >= exp
        return is_expired
    except Exception:
        return True


def _get_auth_headers():
    """Get authentication headers for API requests"""
    global AUTH_TOKEN
    if not AUTH_TOKEN:
        _load_token()
    if not AUTH_TOKEN:
        raise typer.Exit("Not authenticated. Run 'dooers login' first.")
    
    # Check if token is expired
    if _is_token_expired(AUTH_TOKEN):
        typer.echo("❌ Your session has expired. Please login again.")
        _clear_token()
        raise typer.Exit("Session expired. Run 'dooers login' first.")
    
    # Use cookie authentication (dev API prefers cookies)
    headers = {
        "Cookie": f"auth={AUTH_TOKEN}"
    }
    return headers


@app.command()
def login(
    email: str = typer.Option(..., prompt=True, help="Your email address"),
    code: str = typer.Option(None, help="Verification code (if not provided, will prompt)"),
):
    """Authenticate with dooers.ai"""
    global AUTH_TOKEN
    
    # Check if already authenticated
    if not AUTH_TOKEN:
        _load_token()
    if AUTH_TOKEN:
        typer.echo("✅ Already authenticated!")
        typer.echo("   Use 'dooers logout' to logout first if you want to re-authenticate")
        return
    
    # Step 1: Request session (get OTP sent to email)
    typer.echo("Requesting verification code...")
    try:
        request_data = {"email": email, "method": "email"}
        response = requests.post(
            "https://api.dev.dooers.ai/api/v1/session/request",
            json=request_data,
            timeout=10
        )
        
        if response.status_code == 400:
            error_data = response.json()
            error_type = error_data.get("status", {}).get("description", "Unknown error")
            if "AUTH_PROVIDER_ERROR" in error_type:
                typer.echo("❌ Authentication provider error. This might be due to:")
                typer.echo("   - Email already has an active session")
                typer.echo("   - Rate limiting")
                typer.echo("   - Invalid email address")
                typer.echo("   - Try logging out first: dooers logout")
                raise typer.Exit(1)
        
        response.raise_for_status()
        
        session_data = response.json()
        email_id = session_data.get("output", {}).get("email_id")
        
        if not email_id:
            typer.echo("❌ Failed to get email ID from response")
            typer.echo(f"Response structure: {session_data}")
            raise typer.Exit(1)
            
        typer.echo("✅ Verification code sent to your email")
        
        # Step 2: Get OTP code
        if not code:
            code = typer.prompt("Enter the verification code from your email")
        
        # Step 3: Create session with OTP code
        typer.echo("Verifying code...")
        create_response = requests.post(
            "https://api.dev.dooers.ai/api/v1/session/create",
            json={"email_id": email_id, "code": code},
            timeout=10
        )
        create_response.raise_for_status()
        
        session_result = create_response.json()
        
        # Extract token from cookies (the API returns it as 'auth' cookie)
        AUTH_TOKEN = None
        for cookie in create_response.cookies:
            if cookie.name == 'auth':
                AUTH_TOKEN = cookie.value
                break
        
        # Fallback: try to get token from JSON response
        if not AUTH_TOKEN:
            AUTH_TOKEN = session_result.get("output", {}).get("token")
        
        # Additional fallback: check if token is in the response headers
        if not AUTH_TOKEN:
            AUTH_TOKEN = create_response.headers.get("Authorization", "").replace("Bearer ", "")
        
        if AUTH_TOKEN:
            _save_token(AUTH_TOKEN)
            typer.echo("✅ Successfully authenticated!")
        else:
            typer.echo("❌ Authentication failed - no token received")
            raise typer.Exit(1)
            
    except requests.RequestException as e:
        typer.echo(f"❌ Authentication failed: {e}")
        raise typer.Exit(1)


@app.command()
def logout():
    """Logout and clear authentication"""
    global AUTH_TOKEN
    
    if not AUTH_TOKEN:
        _load_token()
    
    if AUTH_TOKEN:
        try:
            requests.post(
                "https://api.dev.dooers.ai/api/v1/session/remove",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=10
            )
        except requests.RequestException:
            pass  # Ignore errors on logout
    
    _clear_token()
    typer.echo("✅ Logged out successfully")


@app.command()
def whoami():
    """Show current user information"""
    try:
        headers = _get_auth_headers()
        response = requests.get(
            "https://api.dev.dooers.ai/api/v1/session/verify",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        user_data = response.json()
        
        # Try to get email from different possible locations
        email = (user_data.get('email') or 
                user_data.get('user', {}).get('email') or 
                user_data.get('output', {}).get('email') or
                'Authenticated User')
        
        typer.echo(f"✅ Authenticated as: {email}")
        
    except Exception as e:
        typer.echo(f"❌ Failed to get user info: {e}")
        raise typer.Exit(1)


def _make_tar_gz_of_cwd() -> str:
    tmpfd, tmppath = tempfile.mkstemp(suffix=".tar.gz", prefix="dooers-")
    os.close(tmpfd)
    
    def load_ignore_patterns() -> list:
        """Load ignore patterns from .dooersignore (gitignore-style) and add sensible defaults.

        Patterns are matched against POSIX-style relative paths ("/" separators).
        Examples:
          - node_modules/
          - .venv/
          - dist/
          - build/
          - *.log
          - data/**
        """
        default_patterns = [
            ".git/",
            ".gitignore",
            ".venv/",
            "venv/",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "dist/",
            "build/",
            "*.log",
        ]
        patterns: list[str] = list(default_patterns)
        ignore_file = Path(".dooersignore")
        if ignore_file.exists():
            for line in ignore_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)
        return patterns

    def is_ignored(rel_path: str, patterns: list) -> bool:
        """Return True if rel_path should be ignored based on patterns.

        - Supports directory patterns ending with '/'
        - Supports glob patterns (via fnmatch)
        - Supports simple segment matches (e.g., 'node_modules')
        """
        posix_path = rel_path.replace(os.sep, "/")
        for pat in patterns:
            pat = pat.strip()
            if not pat:
                continue
            # Directory prefix pattern
            if pat.endswith("/"):
                prefix = pat[:-1]
                if posix_path == prefix or posix_path.startswith(prefix + "/"):
                    return True
            # Anchor from root
            if pat.startswith("/"):
                if fnmatch.fnmatch(posix_path, pat.lstrip("/")):
                    return True
            # Glob match anywhere
            if fnmatch.fnmatch(posix_path, pat):
                return True
            # Segment match (e.g., 'node_modules')
            if "/" not in pat and pat in posix_path.split("/"):
                return True
        return False

    patterns = load_ignore_patterns()

    with tarfile.open(tmppath, "w:gz") as tar:
        for root, dirs, files in os.walk("."):
            relroot = os.path.relpath(root, ".")
            if relroot == ".":
                relroot = ""

            # Prune ignored directories in-place so os.walk doesn't descend into them
            pruned_dirs = []
            for d in list(dirs):
                rel_dir_path = os.path.join(relroot, d) if relroot else d
                if is_ignored(rel_dir_path + "/", patterns):
                    pruned_dirs.append(d)
            for d in pruned_dirs:
                dirs.remove(d)

            for name in files:
                rel_file_path = os.path.join(relroot, name) if relroot else name
                if is_ignored(rel_file_path, patterns):
                    continue
                full = os.path.join(root, name)
                arcname = os.path.relpath(full, ".")
                tar.add(full, arcname=arcname)
    return tmppath


def _start_spinner(message: str):
    """Start a simple CLI spinner in a background thread. Returns a stopper func.

    The spinner writes to stderr to avoid interfering with tqdm's stdout.
    """
    stop_event = threading.Event()

    def run():
        frames = "|/-\\"
        cycle = itertools.cycle(frames)
        while not stop_event.is_set():
            sys.stderr.write(f"\r{message} " + next(cycle))
            sys.stderr.flush()
            time.sleep(0.1)
        # clear line
        sys.stderr.write("\r" + " " * (len(message) + 2) + "\r")
        sys.stderr.flush()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    def stop():
        stop_event.set()
        t.join(timeout=1)

    return stop


@app.command()
def push(
    agent_name: str = typer.Argument(..., help="Agent name"),
    server_url: str = typer.Option(
        "https://api.dooers.ai",
        help="Agent Deploy service base URL (e.g. https://api.dooers.ai)",
    ),
    no_build: bool = typer.Option(
        False,
        "--no-build",
        help="Upload only. Do not trigger Cloud Build after upload.",
    ),
    tag: str = typer.Option("latest", help="Docker image tag to use for the build"),
    environment: str = typer.Option(
        "prod",
        help="Target environment for routing: one of prod, stg, dev",
    ),
    version: str = typer.Option("v1", help="API version segment used in the route"),
):
    """Archive current directory and upload to server to build an image.

    Usage examples:
      - dooers push my-agent
      - dooers push --environment dev my-agent
      - dooers push --no-build my-agent
      - dooers push --tag v0.3.1 my-agent

    Notes:
      - The archive is created from the current working directory.
      - Files can be excluded using a `.dooersignore` file (gitignore-style patterns).
        Defaults ignored: .git/, .venv/, node_modules/, __pycache__/, *.pyc, .DS_Store, dist/, build/, *.log
      - When --no-build is provided, the server will upload the archive to GCS but
        will not trigger Cloud Build.
    """
    # Security warning for HTTP URLs
    if server_url.startswith("http://") and "localhost" not in server_url:
        typer.echo("⚠️  WARNING: Using HTTP instead of HTTPS. This is not secure for production!")
        if not typer.confirm("Continue anyway?"):
            raise typer.Exit(1)
    
    # Validate environment
    if environment not in ["prod", "stg", "dev"]:
        typer.echo(f"❌ Invalid environment: {environment}. Must be one of: prod, stg, dev")
        raise typer.Exit(1)
    
    archive_path = _make_tar_gz_of_cwd()
    try:
        # Build dynamic path: {base_url}/{version}/deploy-service-{environment}/{agent_name}/push
        base_path = f"/{version}/deploy-service-{environment}"
        url = f"{server_url.rstrip('/')}{base_path}/{agent_name}/push"
        with open(archive_path, "rb") as f:
            size = os.path.getsize(archive_path)
            with tqdm(total=size, unit='B', unit_scale=True, desc='Uploading') as pbar:
                class TqdmFile(io.BufferedReader):
                    def read(self, *args, **kwargs):
                        chunk = super().read(*args, **kwargs)
                        if chunk:
                            pbar.update(len(chunk))
                        return chunk
                tf = TqdmFile(f)
                files = {"archive": (Path(archive_path).name, tf, "application/gzip")}
                params = {"build": str(not no_build).lower(), "image_tag": tag}
                headers = _get_auth_headers()
                stop_spin = _start_spinner("Processing on server…")
                try:
                    resp = requests.post(
                        url,
                        files=files,
                        params=params,
                        headers=headers,
                        timeout=600,
                    )
                finally:
                    stop_spin()
                resp.raise_for_status()
                typer.echo(resp.json())
    finally:
        try:
            os.remove(archive_path)
        except OSError:
            pass


if __name__ == "__main__":
    app()
