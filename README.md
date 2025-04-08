# Reassembly

An application to reassemble fractured objects: specifically cultural heritage

# Run

## Pre-requisites (not complete)

```
cmake
gcc
```

## Step 1: Download pre-compiled Open3D binary package

Download the pre-compiled Open3D binary package from the [Open3D release page](https://github.com/isl-org/Open3D/releases). The binary package is available for Ubuntu (with and without CUDA), macOS (Inel and Apple Si), and Windows. You may download a stable release or a development build (devel-main).

Extract the pre-compiled binary to a path (_OPEN3D_ROOT_) of your choice

## Step 2: Use Open3D in this project

On Ubuntu/macOS: (only tested on linux)

```
# Make the scripts executable
chmod +x ./build.sh
chmod +x ./run.sh
```

```
# Run needed scripts
build.sh (set the OPEN3D_ROOT in build script)
run.sh
```

On Windows: (not tested)

```batch
mkdir build
cmake -DOpen3D_ROOT=OPEN3D_ROOT ..
cmake --build . --config Release --parallel 4
Release\App
```
