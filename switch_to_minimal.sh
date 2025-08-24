#!/bin/bash
# Script to switch to minimal FastAPI app for testing

echo "Switching to minimal FastAPI app..."

# Backup current files
if [ -f "Procfile" ]; then
    mv Procfile Procfile_backup
    echo "Backed up Procfile to Procfile_backup"
fi

if [ -f "requirements.txt" ]; then
    mv requirements.txt requirements_backup.txt
    echo "Backed up requirements.txt to requirements_backup.txt"
fi

# Switch to minimal versions
mv Procfile_minimal Procfile
mv requirements_minimal.txt requirements.txt

echo "✅ Switched to minimal app"
echo "Now run: git add . && git commit -m 'Switch to minimal test app' && git push"
