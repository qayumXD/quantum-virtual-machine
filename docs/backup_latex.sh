#!/bin/bash
# FYP LaTeX Backup Script
# Creates timestamped backup of LaTeX files

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups/latex_backup_$TIMESTAMP"

echo "Creating backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy LaTeX files
cp -r docs/fyp_latex "$BACKUP_DIR/"

# Copy planning documents
cp docs/fyp_latex_execution_plan.md "$BACKUP_DIR/"
cp docs/fyp_latex_preparation_analysis.md "$BACKUP_DIR/"
cp docs/phase1_progress.md "$BACKUP_DIR/"
cp docs/CURRENT_STATUS.md "$BACKUP_DIR/"

# Create ZIP archive
cd backups
zip -r "latex_backup_$TIMESTAMP.zip" "latex_backup_$TIMESTAMP"
cd ..

echo "✅ Backup created: backups/latex_backup_$TIMESTAMP.zip"
echo "✅ Backup folder: $BACKUP_DIR"
