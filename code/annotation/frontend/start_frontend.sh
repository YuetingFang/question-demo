#!/bin/bash

# Build the React frontend if it hasn't been built already
if [ ! -d "build" ] || [ "$(find src -newer build -print -quit)" ]; then
  echo "Building React frontend..."
  npm run build
else
  echo "Using existing React build"
fi

echo "Frontend build complete."
