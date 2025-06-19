#!/usr/bin/env python3

"""SysHealth - System Health Report Generator

This script collects comprehensive system information from local or remote hosts
and uses Claude AI to analyze the data and generate insightful health reports.
The reports identify critical issues, warnings, and provide recommendations to
improve system health and performance.

The script can analyze multiple hosts in a single run and supports multiple
output languages. Reports are saved as markdown files and can optionally be
emailed to specified recipients.

Requires the Anthropic API key to be set in the ANTHROPIC_API_KEY environment variable.

Usage examples:
  ./syshealth.py -v                      # Analyze current host with verbose output
  ./syshealth.py -v remote-server        # Analyze a remote host
  ./syshealth.py -v -L spanish host1 host2  # Analyze multiple hosts in Spanish
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import smtplib
import socket
import subprocess
import sys
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Union

# Import our Claude client
from claude_client import ClaudeClient

# Import configuration management
from config import (
    get_config, get_claude_model, get_default_language, 
    get_output_directory, get_log_format
)

# Constants
VERSION = "1.0.0"  # Current version of SysHealth

# Configure logging - default to WARNING level, verbose mode will change to INFO
logging.basicConfig(
  level=logging.WARNING,
  format=get_log_format()
)
logger = logging.getLogger("syshealth")

def parse_arguments():
  """Parse command line arguments for SysHealth.
  
  Sets up all available command-line options including verbose/debug modes,
  output language, model selection, output directory, email recipients,
  and list of hosts to analyze.
  
  Returns:
      argparse.Namespace: Parsed command-line arguments
  """
  # Get default output directory from configuration
  default_output_dir = get_output_directory()
  
  parser = argparse.ArgumentParser(
    prog="syshealth",
    description="Generate system health report for local or remote hosts."
  )
  parser.add_argument(
    "-v", "--verbose", 
    action="store_true", 
    help="Enable verbose output including printing reports to terminal"
  )
  parser.add_argument(
    "-d", "--debug", 
    action="store_true", 
    help="Enable debug mode (logs API prompts and additional details)"
  )
  parser.add_argument(
    "-L", "--language", 
    default=get_default_language(),
    help=f"Report language (default: {get_default_language()}; supports all major languages)"
  )
  parser.add_argument(
    "-m", "--model",
    default=get_claude_model(),
    help=f"Claude model to use (default: {get_claude_model()})"
  )
  parser.add_argument(
    "-o", "--output-dir",
    default=default_output_dir,
    help=f"Directory to save reports (default: {default_output_dir})"
  )
  parser.add_argument(
    "--mail",
    help="Comma-separated list of email addresses to send the report to (requires local SMTP server)"
  )
  parser.add_argument(
    "hosts", 
    nargs="*", 
    default=[socket.gethostname()],
    help="Host(s) to analyze (default: current host; remote hosts require SSH key access)"
  )
  return parser.parse_args()

def check_dependencies():
  """Check if required and recommended system dependencies are installed.
  
  Verifies the presence of essential and recommended command-line tools
  that are used to gather system information. The script will exit if
  required dependencies are missing, and will warn if recommended
  dependencies are missing.
  
  Dependencies are loaded from configuration file.
  
  Raises:
      SystemExit: If any required dependencies are missing
  """
  config = get_config()
  required = config.get('dependencies.required', ["python3"])
  recommended = config.get('dependencies.recommended', ["lshw", "df", "ps", "cat", "free"])
  
  missing_required = []
  missing_recommended = []
  
  # Check required dependencies
  for dep in required:
    if shutil.which(dep) is None:
      missing_required.append(dep)
  
  # Exit if required dependencies are missing
  if missing_required:
    logger.error(f"Missing required dependencies: {', '.join(missing_required)}")
    logger.info("Install with: sudo apt-get install " + " ".join(missing_required))
    sys.exit(1)
  
  # Check recommended dependencies
  for dep in recommended:
    if shutil.which(dep) is None:
      missing_recommended.append(dep)
  
  # Just warn about recommended dependencies
  if missing_recommended:
    logger.warning(f"Missing recommended dependencies: {', '.join(missing_recommended)}")
    logger.info("For better results, install: sudo apt-get install " + " ".join(missing_recommended))

def execute_command(command: str, host: Optional[str] = None) -> str:
  """Execute a shell command locally or on a remote host.
  
  This function handles both local command execution and remote execution
  via SSH. It captures command output and handles errors appropriately.
  For remote execution, SSH key-based authentication is expected to be
  already configured.
  
  Args:
      command (str): The shell command to execute
      host (Optional[str]): The hostname to run the command on; if None or
          matches the local hostname, executes locally
  
  Returns:
      str: The command output (stdout) if successful, or error message
          if the command fails
  
  Note:
      - For local execution, shell=True is used to support pipes and redirects
      - For remote execution, the command is passed as an argument to ssh
      - Non-zero exit codes are handled gracefully with warning logs
  """
  try:
    if host and host != socket.gethostname():
      # For SSH remote execution, pass the entire command as a single string
      full_cmd = ["ssh", host, command]
      shell = False
    else:
      # For local execution with pipes and redirects, use shell=True
      full_cmd = command
      shell = True
    
    result = subprocess.run(
      full_cmd,
      capture_output=True,
      text=True,
      check=False,  # Don't raise exception on non-zero exit
      shell=shell
    )
    
    if result.returncode != 0:
      logger.warning(f"Command returned non-zero exit status: {command}")
      return f"Error: {result.stderr}"
    
    return result.stdout
  except Exception as e:
    logger.warning(f"Command failed: {command} - {e}")
    return f"Error executing command: {str(e)}"

def collect_system_info(host: str) -> Dict:
  """Collect comprehensive system information from a host using modular collectors.
  
  This function has been refactored to use specialized collector classes for better
  maintainability, testability, and modularity. Each collector focuses on a specific
  aspect of system information.
  
  Args:
      host (str): The hostname to collect information from (local or remote)
  
  Returns:
      Dict: A dictionary containing all collected system information keyed by
          category. Each value is typically the text output of a command.
  
  Categories of information collected:
      - Basic system: hostname, timestamp, uname, OS release, uptime
      - Hardware: system components listing, CPU, memory
      - Storage: disk usage, block devices, health, mount configuration
      - Processes: top CPU and memory consuming processes
      - Network: interfaces, listening ports
      - Security: failed services, logs, updates, security checks
  """
  logger.info(f"Collecting system information from {host}...")
  
  # Import collectors here to avoid circular imports
  from collectors import (
    BasicSystemInfoCollector,
    HardwareInfoCollector, 
    StorageInfoCollector,
    ProcessInfoCollector,
    NetworkInfoCollector,
    SecurityInfoCollector
  )
  from executors import LocalCommandExecutor, RemoteCommandExecutor
  from config import DEFAULT_COMMANDS
  
  # Determine the appropriate executor based on host
  if host and host != socket.gethostname():
    executor = RemoteCommandExecutor(host)
  else:
    executor = LocalCommandExecutor()
  
  # Create collector instances with dependency injection
  basic_collector = BasicSystemInfoCollector(executor, host, DEFAULT_COMMANDS)
  hardware_collector = HardwareInfoCollector(executor, DEFAULT_COMMANDS) 
  storage_collector = StorageInfoCollector(executor, DEFAULT_COMMANDS)
  process_collector = ProcessInfoCollector(executor, DEFAULT_COMMANDS)
  network_collector = NetworkInfoCollector(executor, DEFAULT_COMMANDS)
  security_collector = SecurityInfoCollector(executor, DEFAULT_COMMANDS)
  
  # Collect information from each specialized collector
  system_info = {}
  
  try:
    system_info.update(basic_collector.collect())
    logger.debug("Basic system information collected")
  except Exception as e:
    logger.warning(f"Failed to collect basic system info: {e}")
  
  try:
    system_info.update(hardware_collector.collect())
    logger.debug("Hardware information collected")
  except Exception as e:
    logger.warning(f"Failed to collect hardware info: {e}")
  
  try:
    system_info.update(storage_collector.collect())
    logger.debug("Storage information collected")
  except Exception as e:
    logger.warning(f"Failed to collect storage info: {e}")
  
  try:
    system_info.update(process_collector.collect())
    logger.debug("Process information collected")
  except Exception as e:
    logger.warning(f"Failed to collect process info: {e}")
  
  try:
    system_info.update(network_collector.collect())
    logger.debug("Network information collected")
  except Exception as e:
    logger.warning(f"Failed to collect network info: {e}")
  
  try:
    system_info.update(security_collector.collect())
    logger.debug("Security information collected")
  except Exception as e:
    logger.warning(f"Failed to collect security info: {e}")
  
  return system_info

def call_claude_api(system_info: Dict, language: str, model: str, debug: bool = False, output_dir: str = None) -> str:
  """Call Claude API to analyze system information and generate a health report.
  
  Creates a Claude client instance, sends the collected system information
  for analysis, and returns the generated health report. In debug mode,
  saves the prompt sent to Claude to a file for troubleshooting.
  
  Args:
      system_info (Dict): The collected system information dictionary
      language (str): The language code for the report (e.g., 'en', 'es')
      model (str): The Claude model to use for analysis
      debug (bool, optional): Whether to save the prompt to a file. Defaults to False.
      output_dir (str, optional): Directory to save debug files. Required if debug=True.
  
  Returns:
      str: The generated health report in markdown format
  
  Note:
      Requires the ANTHROPIC_API_KEY environment variable to be set
  """
  logger.info(f"Calling Claude API with model: {model}")
  
  # Create the Claude client
  client = ClaudeClient(model=model)
  
  # Analyze the system
  response = client.analyze_system(system_info, language)
  
  # If in debug mode and output_dir is provided, save the prompt to a file
  if debug and output_dir:
    # Generate the prompt
    prompt = client._generate_prompt(system_info, language)
    
    # Create debug directory
    config = get_config()
    debug_subdir = config.get('output.debug_subdirectory', 'debug')
    debug_dir = os.path.join(output_dir, debug_subdir)
    os.makedirs(debug_dir, exist_ok=True)
    
    # Save the prompt to a file
    timestamp_format = config.get('output.timestamp_format', '%Y%m%d-%H%M%S')
    debug_extension = config.get('output.file_extensions.debug', '.txt')
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    hostname = system_info.get("hostname", "unknown")
    prompt_file = os.path.join(debug_dir, f"{hostname}-{language}-prompt-{timestamp}{debug_extension}")
    
    with open(prompt_file, "w") as f:
      f.write(prompt)
    
    logger.debug(f"Saved prompt to: {prompt_file}")
  
  return response

def save_report(report: str, host: str, output_dir: str, language: str) -> str:
  """Save the generated health report to a markdown file.
  
  Creates the output directory if it doesn't exist, and saves the report
  with a filename that includes the hostname, language, and timestamp.
  
  Args:
      report (str): The health report content to save
      host (str): The hostname the report is for
      output_dir (str): Directory to save the report
      language (str): The language code of the report
  
  Returns:
      str: The absolute path to the saved report file
  
  Example filename format: hostname-en-20250515-072617.md
  """
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  
  config = get_config()
  timestamp_format = config.get('output.timestamp_format', '%Y%m%d-%H%M%S')
  file_extension = config.get('output.file_extensions.report', '.md')
  
  timestamp = datetime.datetime.now().strftime(timestamp_format)
  filename = f"{host}-{language}-{timestamp}{file_extension}"
  filepath = os.path.join(output_dir, filename)
  
  with open(filepath, "w") as f:
    f.write(report)
  
  return filepath

def send_email(report_path: str, recipients: List[str], host: str) -> bool:
  """Send the system health report via email to the specified recipients.
  
  Reads the report file, converts markdown to HTML using pandoc, and sends
  an email with both HTML content and the original markdown file attached.
  
  Args:
      report_path (str): Path to the markdown report file
      recipients (List[str]): List of email addresses to send the report to
      host (str): The hostname the report is about (used in subject line)
  
  Returns:
      bool: True if email was sent successfully, False otherwise
  
  Requirements:
      - Local SMTP server running on localhost
      - pandoc installed for markdown to HTML conversion (falls back to plain text)
  
  Note:
      The email includes both HTML formatted content and a markdown attachment
  """
  try:
    # Get the report content
    with open(report_path, "r") as f:
      report_content = f.read()
    
    # Get the hostname for this machine
    sender_hostname = socket.gethostname()
    
    # Create a temporary file for HTML conversion
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as html_file:
      html_path = html_file.name
    
    # Convert markdown to HTML using pandoc
    try:
      subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html", "-o", html_path],
        input=report_content,
        text=True,
        check=True
      )
      
      with open(html_path, "r") as f:
        html_content = f.read()
      
      os.unlink(html_path)  # Clean up the temporary file
    except Exception as e:
      logger.warning(f"Failed to convert markdown to HTML: {e}")
      html_content = f"<pre>{report_content}</pre>"  # Fallback if pandoc fails
    
    # Create the email message
    config = get_config()
    sender_name = config.get('email.sender.name', 'SysHealth')
    domain_suffix = config.get('email.sender.domain_suffix', '@hostname').replace('@hostname', f'@{sender_hostname}')
    subject_template = config.get('email.subject_template', 'System Health Report for {hostname}')
    
    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <syshealth{domain_suffix}>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject_template.format(hostname=host)
    
    # Add HTML version of the report
    msg.attach(MIMEText(html_content, "html"))
    
    # Attach the original markdown file
    filename = os.path.basename(report_path)
    attachment = MIMEText(report_content)
    attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(attachment)
    
    # Send the email using SMTP server from configuration
    config = get_config()
    smtp_host = config.get('email.smtp.host', 'localhost')
    smtp_port = config.get('email.smtp.port', 25)
    smtp_timeout = config.get('email.smtp.timeout', 30)
    
    with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as smtp:
      smtp.send_message(msg)
    
    logger.info(f"Report sent via email to: {', '.join(recipients)}")
    return True
  except Exception as e:
    logger.error(f"Failed to send email: {e}")
    return False

def main():
  """Main function to run the system health report generation process.
  
  This function orchestrates the entire workflow:
  1. Parse command-line arguments
  2. Configure logging based on verbosity settings
  3. Check for required system dependencies
  4. Create the output directory
  5. For each specified host:
     a. Collect system information
     b. Call Claude API to analyze and generate a report
     c. Save the report to a file
     d. Display the report if verbose mode is enabled
  6. Send reports via email if requested
  
  The function exits with non-zero status if critical errors occur.
  
  Returns:
      None
  
  Raises:
      SystemExit: If required dependencies are missing or the output directory 
          cannot be created
  """
  args = parse_arguments()
  
  # Set up logging based on flags
  if args.debug:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")
  elif args.verbose:
    logger.setLevel(logging.INFO)
    logger.info("Verbose mode enabled")
  
  check_dependencies()
  
  # Create output directory if it doesn't exist
  try:
    os.makedirs(args.output_dir, exist_ok=True)
  except Exception as e:
    logger.error(f"Failed to create output directory {args.output_dir}: {e}")
    sys.exit(1)
    
  # List to store paths of all generated reports
  report_paths = []
  
  for host in args.hosts:
    logger.info(f"Analyzing host: {host}")
    
    # Collect system information
    system_info = collect_system_info(host)
    
    # Call Claude API with system info and debug flag
    report = call_claude_api(
      system_info, 
      args.language, 
      args.model, 
      debug=args.debug, 
      output_dir=args.output_dir
    )
    
    # Save report with the new naming format
    report_path = save_report(report, host, args.output_dir, args.language)
    report_paths.append((host, report_path))
    
    logger.info(f"Report saved to: {report_path}")
    
    # Display report if verbose
    if args.verbose:
      print("\n" + "=" * 80)
      print(f"HEALTH REPORT FOR {host}:")
      print("=" * 80)
      print(report)
      print("=" * 80)
  
  # Send email if requested
  if args.mail:
    recipients = [email.strip() for email in args.mail.split(",")]
    for host, report_path in report_paths:
      if send_email(report_path, recipients, host):
        logger.info(f"Email sent successfully for host: {host}")
      else:
        logger.error(f"Failed to send email for host: {host}")
  
  logger.info("All reports generated successfully")

if __name__ == "__main__":
  main()

#fin