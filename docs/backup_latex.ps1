# FYP LaTeX Backup Script (PowerShell)
# Creates timestamped backup of LaTeX files

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups/latex_backup_$timestamp"

Write-Host "Creating backup: $backupDir"

# Create backup directory
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

# Copy LaTeX files
Copy-Item -Path "docs/fyp_latex" -Destination "$backupDir/" -Recurse

# Copy planning documents
Copy-Item -Path "docs/fyp_latex_execution_plan.md" -Destination "$backupDir/"
Copy-Item -Path "docs/fyp_latex_preparation_analysis.md" -Destination "$backupDir/"
Copy-Item -Path "docs/phase1_progress.md" -Destination "$backupDir/"
Copy-Item -Path "docs/CURRENT_STATUS.md" -Destination "$backupDir/"

# Create ZIP archive
Compress-Archive -Path $backupDir -DestinationPath "backups/latex_backup_$timestamp.zip"

Write-Host "✅ Backup created: backups/latex_backup_$timestamp.zip" -ForegroundColor Green
Write-Host "✅ Backup folder: $backupDir" -ForegroundColor Green
