#!/bin/bash

# Define installation directory of Open3D
OPEN3D_ROOT="${HOME}/dev/reassembly/open3d_install/cpp"

# From here on out change if you really want

# Define the build directory
BUILD_DIR="build"

# Create the build directory if it doesn't exist
if [ ! -d "$BUILD_DIR" ]; then
  echo "Creating build directory..."
  mkdir "$BUILD_DIR"
fi

# Navigate to the build directory
cd "$BUILD_DIR" || exit

# Run CMake to configure the project (passing Open3D_ROOT if necessary)
echo "Running CMake configuration..."
cmake -DOpen3D_ROOT="$OPEN3D_ROOT" -DCMAKE_EXPORT_COMPILE_COMMANDS=1 ../cpp

# Build the project using make with 12 parallel jobs
echo "Building the project using make..."
make -j 4

# Check if build was successful
if [ $? -ne 0 ]; then
  echo "Build failed. Exiting."
  exit 1
else
  echo "Build successful."
fi
