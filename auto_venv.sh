#!/bin/bash
# Automatically activate the virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
  source ./venv/bin/activate
fi