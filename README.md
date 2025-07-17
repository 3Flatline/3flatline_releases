# 3flatline_releases
Release repositiy and bug tracker for 3flatline cli, server, and community edition


## Install Instructions

3Flatline consists of 3 files: the server, the server config, and the cli.

Unzip the package but leave all of the files intact as they use relative paths for reference.

### Configuration Setup

To configure the system, you need to create a `config.ini` file. Follow these steps:

1. Copy the example configuration file:
   ```bash
   cp config.ini.example config.ini
   ```

2. Edit the `config.ini` file with your 3flatline api key (called wintermute api key in the config file) and your openai api key:

3. Turn on or off Exploits based on your needs.

### Dependencies

[rizin](https://github.com/rizinorg) must be installe and added to the path to process assembly files.

## Usage

1. **Start the server** with your configuration:
   ```bash
   ./3flatline-server -config config.ini
   ```

2. **Use the CLI** to interact with the server:
   ```bash
   ./3flatline-cli
   ```

3. **Web interface** is also available at at `http://localhost:7270`

# REST API

Two main endpoints are available:

**Scan a file:**
```bash
curl -X POST http://localhost:7270/scanfile \
  -H "Content-Type: application/json" \
  -d '{"filePath":"path/to/file"}'
```

**Export results:**
```bash
curl -X GET "http://localhost:7270/api/export/netsage" -o export.json
```

## Local Models

If you want to keep the model local, then run the `install_ollama.sh` script on every endpoint you want to host a model on. Then be sure to update the `config.ini` file with a list of endpoints that you have ollama running on.

To use local models with Ollama:

1. **Install Ollama** on your endpoints:
   ```bash
   ./scripts/install_ollama.sh
   ```

2. **Update configuration** with your Ollama endpoints:
   ```ini
   [loadbalancer]
       endpoints=localhost,server2
   ```

## Database Management

### Database Behavior

When you first run 3flatline-server, it will create a database. If the sever crashes, do not scan the same files again. The state of scanned files is in the database. Anything that didnt complete, will pick right back up after you run the server again. After a scan, it is recommended that you rename the database. Everytime you run the server, if a database doesnt exist then it will be created. This makes it easy to run a scan, change the database name, run a new scan with a new database etc. This can keep the database from becoming to unwieldly or large.

- Database is created automatically on first run
- Scans resume from where they left off after restarts
- Completed scans are stored persistently

### Best Practices

1. **Rename databases** after scans to keep them organized:
   ```bash
   mv database.sqlite project1_scan_$(date +%Y%m%d).sqlite
   ```

2. **Multiple databases** for different projects:
   ```bash
   ./3flatline-server config.ini  # Creates new database.sqlite
   # Scan project A
   mv database.sqlite projectA.sqlite

   ./3flatline-server config.ini  # Creates new database.sqlite
   # Scan project B
   mv database.sqlite projectB.sqlite
   ```

## Known issues:
1. After selecting a directory or file to scan in the cli, sometimes the cli will hang at the loading screen. Enter 'q' to return to the main screen. The jobs were created properly and the scans will execute. The bug is in how the loading screen doesnt properly return you to the home screen.
1. Assembly is implemented in models and neural nets but is not currently user facing.
1. The analysis process is constantly creating and deleting tasks as it moves from coarse to fine grained analysis. This reflects in the CLI progress bar sometimes saying 100% complete before the machine creates more tasks.
