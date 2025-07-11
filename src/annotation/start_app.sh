#!/bin/bash

# Start Flask backend in the background
echo "Starting Flask backend on port 5001..."
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2
echo "Backend started with PID: $BACKEND_PID"

# Build the React frontend if it hasn't been built already
if [ ! -d "build" ] || [ "$(find src -newer build -print -quit)" ]; then
  echo "Building React frontend..."
  npm run build
else
  echo "Using existing React build"
fi

echo "Flask server is running and serving the React frontend at http://localhost:5001"
echo "Press Ctrl+C to stop the server."

# Function to clean up processes on exit
cleanup() {
    echo "Shutting down server..."
    kill $BACKEND_PID
    exit 0
}

# Set up the trap to catch SIGINT (Ctrl+C)
trap cleanup SIGINT

# Keep the script running
wait
