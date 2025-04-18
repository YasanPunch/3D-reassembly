#!/bin/bash

# Define the build directory
BUILD_DIR="build"

# Check if the executable exists in the build directory
if [ ! -f "$BUILD_DIR/App" ]; then
  echo "Executable 'App' not found. Please build the project first using 'build.sh'."
  exit 1
fi

# Run the executable with command-line arguments
echo "Running the executable..."
cd "$BUILD_DIR" || exit
./App "$@" # Pass all arguments to App

# Check if the executable ran successfully
if [ $? -eq 0 ]; then
  echo "Application ran successfully."
else
  echo "Application did not run successfully."
  exit 1
fi
