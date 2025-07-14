# 3Flatline Frontend

## Overview
This is the web interface for the 3Flatline Vulnerability Scanner. It provides a simple, user-friendly way to interact with the 3Flatline scanning engine, allowing you to scan files and directories for potential vulnerabilities and view detailed reports.

## Getting Started

### Prerequisites
- The 3Flatline server must be running locally
- A modern web browser (Chrome, Firefox, Safari, Edge)

### Running the Application

1. Start the 3Flatline server:
   ```
   # From the 3Flatline root directory
   go run main.go
   ```

2. Access the web interface:
   - Open your browser and navigate to: `http://localhost:7270`
   - The frontend will automatically be served by the local server

## Features

### Dashboard
- Real-time statistics of scan tasks and vulnerability reports
- Updates automatically every 10 seconds

### File Scanning
- Scan individual files for vulnerabilities
- Scan entire directories (with automatic filtering of unsupported files)
- Progress indicators for ongoing scans

### Results Viewing
- Browse scanned files
- View vulnerabilities detected in each file
- Filter files by name
- Detailed vulnerability reports including:
  - Vulnerability class/type
  - Description of the vulnerability
  - The vulnerable code snippet
  - Recommended fixes

## How to Use

### Scanning Files
1. In the "Scan Files" section, enter the absolute path to the file you want to scan
2. Click "Scan File"
3. Wait for the scan to complete

### Scanning Directories
1. In the "Scan Directory" section, enter the absolute path to the directory
2. Click "Scan Directory"
3. The system will automatically scan all supported files in the directory (skipping test files and unsupported file types)

### Viewing Results
1. After scanning, the files will appear in the "Scanned Files" list
2. Click on a file to view its vulnerabilities
3. Click on a vulnerability card to see detailed information
4. You can delete a vulnerability report if needed from the details modal

## Supported File Types
The scanner supports multiple programming languages including:
- C/C++
- Python
- JavaScript/TypeScript
- Java
- Go
- Ruby
- PHP
- C#
- Rust
- Solidity
- And more

## Troubleshooting

### File Not Found
- Make sure you're using absolute paths
- Verify that the path exists and is accessible by the server

### No Vulnerabilities Showing
- Confirm that the file was successfully scanned
- Some files may not have any detected vulnerabilities

### Server Connection Issues
- Verify that the 3Flatline server is running on port 8080
- Check for any error messages in the server console

## License
See the main 3Flatline repository for license information.
