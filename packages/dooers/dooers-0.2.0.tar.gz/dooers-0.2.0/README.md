# Dooers CLI

A command-line tool for deploying AI agents to the Dooers platform.

## Installation

### From PyPI (Recommended)
```bash
pip install dooers
```

### From Source
```bash
git clone https://github.com/your-org/dooers-cli.git
cd dooers-cli
pip install -e .
```

## Quick Start

1. **Login to your account:**
   ```bash
   dooers login --email your@email.com
   ```

2. **Check your authentication status:**
   ```bash
   dooers whoami
   ```

3. **Deploy your agent:**
   ```bash
   dooers push my-agent
   ```

4. **Logout when done:**
   ```bash
   dooers logout
   ```

## Commands

### `dooers login`
Authenticate with your Dooers account using email and OTP verification.

```bash
dooers login --email your@email.com
```

### `dooers whoami`
Check your current authentication status and user information.

```bash
dooers whoami
```

### `dooers push`
Deploy your agent code to the Dooers platform.

```bash
dooers push <agent-name> [options]

Options:
  --server-url TEXT     Agent Deploy service URL (default: http://localhost:8080)
  --no-build           Do not trigger build after upload
  --tag TEXT           Image tag (default: latest)
```

### `dooers logout`
Clear your authentication session.

```bash
dooers logout
```

## Examples

### Deploy an agent with custom tag
```bash
dooers push my-agent --tag v1.0.0
```

### Upload without building
```bash
dooers push my-agent --no-build
```

### Use custom server URL
```bash
dooers push my-agent --server-url https://api.dooers.ai
```

## Requirements

- Python 3.9+
- Valid Dooers account
- Agent code with a `Dockerfile`

## Support

For support, visit [https://dooers.ai](https://dooers.ai) or contact support@dooers.ai