# App Sync - Aurica Package Manager

⚠️ **PROPRIETARY SOFTWARE - READ BEFORE USE** ⚠️

This software is proprietary. Public availability does NOT grant any rights to use.
Commercial use requires explicit permission from the owner.
Users must understand and accept the license terms before use.

See LICENSE file for full terms and conditions.

---

Application package management service for the Aurica platform.

## Features

- Install apps from PyPI and npm registries
- Publish apps to GitHub
- List installed applications
- Uninstall applications
- Version management

## Installation

Install via package manager:

```bash
pip install avyas-app-sync
# or
npm install @avyas/app-sync
```

## API Endpoints

### Install App
```
POST /api/install
```

Install an application from a package registry.

**Request:**
```json
{
  "package_ref": "avyas/aurica-base-apps/weather-app:1.0.0",
  "force": false
}
```

### List Installed Apps
```
GET /api/installed
```

Returns list of all installed applications.

### Publish App
```
POST /api/publish
```

Publish an app to GitHub repository.

**Request:**
```json
{
  "app_name": "weather-app",
  "commit_message": "Update to v1.1.0",
  "tag": "weather-app-v1.1.0",
  "push": true
}
```

## License

**PROPRIETARY LICENSE**

Copyright (c) 2025 Amit Vyas (avyas). All rights reserved.

- ❌ No license granted for any use
- ❌ Commercial use prohibited without written agreement
- ❌ Personal use requires permission
- ⚠️ Use at your own risk - understand what you're getting into

Contact: https://github.com/avyas

See LICENSE file for complete terms.
