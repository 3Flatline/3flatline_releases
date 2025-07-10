# 3flatline_releases
Release repositiy and bug tracker for 3flatline cli, server, and community edition


## Install Instructions

3Flatline consists of 3 files: the server, the server config, and the cli.

First run the server. It takes one argument, the config file. Set the proper API keys in the config file first. You will need an API for 3flatline and for OpenAI.

`./3flatline-server config.ini`

Then run the cli to interact with the server or call the rest API.

`./3flatline-cli`

### Docker install

### Configuration Setup

To configure the system, you need to create a `config.ini` file. Follow these steps:

1. Copy the example configuration file:
   ```bash
   cp config.ini.example config.ini
   ```

2. Edit the `config.ini` file with your 3flatline api key (called wintermute api key in the config file) and your openai api key:

3. Turn on or off Exploits based on your needs.

## Web app

Go to `localhost:7270` for a quick view of results or to have a GUI interface to scan files or directories.

## Rest API:
There is currently only two endpoints. One to scan a file and one to export the database to a json. Here is the associated curl

### Scan file

```bash
curl -X POST http://localhost:7270/scanfile \
  -H "Content-Type: application/json" \
  -d '{"filePath":"path/to/file"}'
```

### Export Json

```bash
curl -X GET "http://localhost:7270/api/export/netsage" -o export.json
```

## Local Models

If you want to keep the model local, then run the `install_ollama.sh` script on every endpoint you want to host a model on. Then be sure to update the `config.ini` file with a list of endpoints that you have ollama running on.

## The database

When you first run 3flatline-server, it will create a database. If the sever crashes, do not scan the same files again. The state of scanned files is in the database. Anything that didnt complete, will pick right back up after you run the server again. After a scan, it is recommended that you rename the database. Everytime you run the server, if a database doesnt exist then it will be created. This makes it easy to run a scan, change the database name, run a new scan with a new database etc. This can keep the database from becoming to unwieldly or large.


## Known issues:
1. After selecting a directory or file to scan in the cli, sometimes the cli will hang at the loading screen. Enter 'q' to return to the main screen. The jobs were created properly and the scans will execute. The bug is in how the loading screen doesnt properly return you to the home screen.
1. Assembly is implemented in models and neural nets but is not currently user facing.
1. The analysis process is constantly creating and deleting tasks as it moves from coarse to fine grained analysis. This reflects in the CLI progress bar sometimes saying 100% complete before the machine creates more tasks.
