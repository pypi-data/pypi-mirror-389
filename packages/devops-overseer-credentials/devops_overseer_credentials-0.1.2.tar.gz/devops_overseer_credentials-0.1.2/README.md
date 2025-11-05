
# 🧩 devops-overseer-credentials

**`devops-overseer-credentials`** is a plugin extension for the [DevOps Overseer](https://github.com/your-org/devops-overseer) framework.  
It provides a simple and consistent command-line interface for securely managing local credentials (usernames, tokens, authentication types) used by other DevOps Overseer adapters or automation scripts.

---

## 🚀 Overview

This plugin allows you to:
- **Add**, **update**, or **remove** credentials for applications and services (e.g., Jira, Confluence, Artifactory).
- Store credentials locally in a structured YAML file under `~/.config/devops-overseer/credentials.yml`.
- Manage multiple credentials under distinct application names.
- Integrate with the Overseer CLI using the command:
  ```bash
  devopso credentials [command] [options]
  ```

All credentials are persisted in YAML format and can be consumed by other DevOps Overseer components through the centralized configuration management system.

---

## ⚙️ Installation

If not already bundled within your DevOps Overseer setup:

```bash
pip install devops-overseer-credentials
```

This plugin will automatically register itself as a subcommand in the Overseer CLI if installed within the same Python environment.

---

## 🧠 Usage

### Command syntax

```bash
devopso credentials <command> [options]
```

### Available commands

| Command  | Alias | Description                                    |
| -------- | ----- | ---------------------------------------------- |
| `add`    | `a`   | Add new credentials for an application         |
| `remove` | `rm`  | Remove credentials for an application          |
| `update` | `u`   | Update credentials for an existing application |

### Options

| Option          | Short | Required        | Description                                                                                 |
| --------------- | ----- | --------------- | ------------------------------------------------------------------------------------------- |
| `--application` | `-a`  | ✅               | Target application name (e.g. `jira`, `confluence`)                                         |
| `--user`        | `-u`  | ⚙️ (add/update) | Username or identifier                                                                      |
| `--password`    | `-p`  | ⚙️ (add/update) | Password or API token                                                                       |
| `--type`        | `-t`  | ❌               | Authentication type (`Basic` or `Bearer`, defaults to `Basic`)                              |
| `--file-path`   | `-f`  | ❌               | Path to the credentials YAML file (defaults to `~/.config/devops-overseer/credentials.yml`) |

---

## 💡 Examples

### Add new credentials

```bash
devopso credentials add \
  -a jira \
  -u clement.dourval@example.com \
  -p myapitoken123 \
  -t Basic
```

### Update existing credentials

```bash
devopso credentials update \
  -a confluence \
  -u newuser@example.com \
  -p newapitoken456
```

### Remove credentials

```bash
devopso credentials remove -a artifactory
```

---

## 🧾 Configuration file structure

Credentials are stored in YAML format.
Example `~/.config/devops-overseer/credentials.yml`:

```yaml
apps:
  jira:
    login: clement.dourval@example.com
    api-token: myapitoken123
    auth-type: Basic

  confluence:
    login: user@company.com
    api-token: token456
    auth-type: Bearer
```

---

## 🧱 Internals

### Core class: `CredentialsManager`

Handles all CRUD operations on credentials, including validation and persistence:

* **`validate()`** — ensures required parameters are provided depending on the command.
* **`add_credentials()`** — safely adds a new entry to the YAML configuration.
* **`update_credentials()`** — replaces an existing entry.
* **`remove_credentials()`** — deletes credentials for a given application.
* **`run()`** — orchestrates operations based on the parsed CLI command.

### Logging

All plugin operations integrate with the main `devopso` CLI logging system, preserving consistent formatting and verbosity.

---

## 🧩 Integration with DevOps Overseer

This plugin registers automatically via:

```python
def register(subparsers):
    ...
```

When the Overseer CLI loads, it detects and integrates all available plugins through the `devopso.plugins` entry point group.

---

## ⚠️ Error Handling

| Condition                                        | Error Message                                          | Behavior                    |
| ------------------------------------------------ | ------------------------------------------------------ | --------------------------- |
| Missing user/password for add/update             | `'user' and 'password' are required for this command.` | Process exits with code `1` |
| Trying to add existing application               | `can't add already existing application`               | Raises `ConfigurationError` |
| Trying to update/remove non-existing application | `nothing to update/remove`                             | Process exits with code `1` |

---

## 🧰 Dependencies

* `devopso.core.configuration` — Configuration management utilities
* `devopso.adapters.atlassian_adapter` — Optional dependency for extended integrations
* `devopso.cli` — Main CLI interface for command registration and logging

---

## 🪪 License

This project is part of the **DevOps Overseer** ecosystem.
All rights reserved © 2025 — Licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Clement Dourval**
📧 [dourval.clement@gmail.com](mailto:dourval.clement@gmail.com)

---

## 🏷️ Keywords

`devops`, `credentials`, `cli`, `configuration`, `plugin`, `yaml`, `automation`, `devops-overseer`

