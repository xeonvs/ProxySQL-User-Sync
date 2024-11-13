# ProxySQL User Sync
[![Python Version](https://img.shields.io/badge/python-3.9+-blue?logo=python)](https://www.python.org/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![License](https://img.shields.io/badge/license-MIT-brightgreen)](https://opensource.org/licenses/MIT)

ProxySQL User Sync is a Python utility for synchronizing users from a MySQL cluster with ProxySQL. It automatically adds users to ProxySQL from MySQL, updating existing records.

---

## Requirements

- Python 3.x
- pymysql library

## Installation

### 1. Manual install the required dependencies
   - ### by package manager
    ```bash
    sudo apt update
    sudo apt install python3-pymysql
    ```
   - ### by PIP
   ```bash
   pip install pymysql
   # or
   pip install -r requirements.txt
   ```

### 2. Clone the repository or download [file](https://github.com/xeonvs/ProxySQL-User-Sync/raw/refs/heads/main/proxysql_user_sync.py)
```bash
git clone https://github.com/xeonvs/proxysql-user-sync.git
cd proxysql-user-sync
```
---

## Configuration

You can set parameters via environment variables or command line arguments. Command line parameters take precedence over environment variables.

### Environment variables

- `PROXYSQL_ADMIN_HOST` - ProxySQL host (default: `localhost`)
- `PROXYSQL_ADMIN_PORT` - ProxySQL port (default: `6032`)
- `PROXYSQL_ADMIN_USER` - ProxySQL username (default: `admin`)
- `PROXYSQL_ADMIN_PASSWORD` - ProxySQL user password (required)
- `PROXYSQL_DEFAULT_HOSTGROUP` - Default ProxySQL host group for users (default: `0`)


- `DB_NODES` - Comma separated MySQL nodes (default: `node1.local,node2.local,node3.local`)
- `DB_USER` - MySQL username (default: `monitor`)
- `DB_PASSWORD` - Password MySQL user (required)
- `DB_PORT` - MySQL port (default: `3306`)


- `APPLY_CHANGES` - Flag to apply changes to ProxySQL (**default: `false`**)

### Command line arguments

- `--proxysql-admin-host` - ProxySQL host
- `--proxysql-admin-port` - ProxySQL port
- `--proxysql-admin-user` - ProxySQL username
- `--proxysql-admin-password` - ProxySQL user password
- `--proxysql-default-hostgroup` - Default ProxySQL host group for added users


- `--db-nodes` - MySQL nodes, separated by comma
- `--db-port` - MySQL port
- `--db-user` - MySQL username
- `--db-password` - MySQL user password


- `--apply` - Flag to apply changes to running ProxySQL (only used when neither `--proxysql-config-update` nor `--export-sql` are specified)
- `--proxysql-config-update <FILE>` - Update ProxySQL config file directly.
- `--export-sql <DIR>` - Export SQL commands to a file in the specified directory.


---

## Usage

Run the script with the required parameters in test mode (by default):

```bash
python3 proxysql_user_sync.py --proxysql-admin-password='your_password' --db-password='your_db_password'
```

Apply changes:
```bash
python3 proxysql_user_sync.py --proxysql-admin-password='your_password' --db-password='your_db_password' --apply
```

Update ProxySQL config directly (requires root privileges or appropriate file permissions):
```bash
sudo python3 proxysql_user_sync.py --proxysql-config-update /etc/proxysql.cnf --db-password='your_db_password'
```

Export SQL commands to a directory (e.g., 'output_sql'):
```bash
mkdir /tmp/output_sql
python3 proxysql_user_sync.py --export-sql /tmp/output_sql --db-password='your_db_password'
```
