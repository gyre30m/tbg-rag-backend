#!/bin/bash
# Script to switch back to full FastAPI app

echo "Switching back to full FastAPI app..."

# Backup minimal files
if [ -f "Procfile" ]; then
    mv Procfile Procfile_minimal
    echo "Backed up minimal Procfile to Procfile_minimal"
fi

if [ -f "requirements.txt" ]; then
    mv requirements.txt requirements_minimal.txt
    echo "Backed up minimal requirements.txt to requirements_minimal.txt"
fi

# Restore full versions
mv Procfile_backup Procfile
mv requirements_backup.txt requirements.txt

echo "✅ Switched back to full app"
echo "Now run: git add . && git commit -m 'Switch back to full app' && git push"
