#!/bin/bash

set -e  # Exit immediately on error

echo "🛠️  Cleaning old build..."
rm -rf build layer

echo "🐳 Building Docker image..."
docker build -t paramiko-layer .

echo "🚀 Running Docker container to extract layer files..."
CONTAINER=$(docker run -d paramiko-layer false)

echo "📦 Copying /opt contents from container to ./build directory..."
docker cp "$CONTAINER":/opt build

echo "🧹 Cleaning up Docker container..."
docker rm "$CONTAINER"

echo "📝 Creating .slsignore file in build directory..."
cat > build/.slsignore << EOF
**/*.a
**/*.la
share/**
include/**
bin/**
EOF

echo "✅ Done! Your Lambda layer is in ./build"

