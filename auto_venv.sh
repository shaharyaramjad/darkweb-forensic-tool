#!/bin/bash
# Automatically activate the virtual environment if not already activated

if [ -z "$VIRTUAL_ENV" ]; then
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # For Git Bash or Cygwin on Windows
    if [ -f "./venv/Scripts/activate" ]; then
      source ./venv/Scripts/activate
    else
      echo "Could not find ./venv/Scripts/activate. Please ensure your virtual environment is set up."
    fi
  else
    # For Unix-like systems (Linux, macOS, WSL)
    if [ -f "./venv/bin/activate" ]; then
      source ./venv/bin/activate
    else
      echo "Could not find ./venv/bin/activate. Please ensure your virtual environment is set up."
    fi
  fi
fi