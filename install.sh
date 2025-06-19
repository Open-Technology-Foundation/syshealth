#!/bin/bash

set -euo pipefail

###############################################################################
# SysHealth Installer Script
#
# This script installs the SysHealth tool to the system, making it available
# for all users. It performs the following actions:
#  1. Copies all files to /usr/local/syshealth
#  2. Creates a symlink in /usr/local/bin
#  3. Sets appropriate permissions
#  4. Creates and configures a Python virtual environment
#  5. Installs required dependencies
#
# Requirements:
#  - sudo privileges
#  - Python 3
#  - Internet connection (for pip package installation)
#
# Usage:
#   ./install.sh
###############################################################################

# Get the directory of this script
declare -r SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing SysHealth..."

# Define the installation directory in a standard system location
declare -r INSTALL_DIR="/usr/local/syshealth"

# Create destination directory if it doesn't exist (requires sudo)
if [[ ! -d "${INSTALL_DIR}" ]]; then
  echo "Creating installation directory ${INSTALL_DIR}..."
  sudo mkdir -p "${INSTALL_DIR}"
fi

# Copy files
echo "Copying files to ${INSTALL_DIR}..."
sudo cp -r "${SCRIPT_DIR}"/* "${INSTALL_DIR}/"

# Create symlink to the main script
echo "Creating symlink in /usr/local/bin..."
sudo ln -sf "${INSTALL_DIR}/syshealth" /usr/local/bin/syshealth

# Set permissions
echo "Setting permissions..."
sudo chmod +x "${INSTALL_DIR}/syshealth"
sudo chmod +x "${INSTALL_DIR}/syshealth.py"

# Create and set up Python virtual environment for isolated dependencies
echo "Setting up Python virtual environment..."
if command -v python3 &>/dev/null; then
  # Create virtual environment in the installation directory
  python3 -m venv "${INSTALL_DIR}/.venv"
  
  # Activate the virtual environment for installing packages
  source "${INSTALL_DIR}/.venv/bin/activate"
  
  # Upgrade pip to the latest version for better package compatibility
  pip install --upgrade pip
  
  # Install required dependencies from requirements.txt
  pip install -r "${INSTALL_DIR}/requirements.txt"
  
  echo "Virtual environment set up successfully at ${INSTALL_DIR}/.venv"
else
  echo "Warning: python3 not found. Please install Python 3 and then run:"
  echo "python3 -m venv ${INSTALL_DIR}/.venv"
  echo "source ${INSTALL_DIR}/.venv/bin/activate"
  echo "pip install -r ${INSTALL_DIR}/requirements.txt"
fi

echo "SysHealth installed successfully!"
echo "Run 'syshealth -v' to generate a system health report."
echo "Remember to set your API key with: export ANTHROPIC_API_KEY='your-api-key'"

#fin