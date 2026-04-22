# LaTeX Compilation Script (PowerShell)
# This script runs pdflatex multiple times to resolve all references

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "FYP LaTeX Compilation Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "Pass 1: Initial compilation..." -ForegroundColor Yellow
pdflatex -interaction=nonstopmode main.tex | Out-Null
Write-Host "✓ Pass 1 complete" -ForegroundColor Green

Write-Host "Pass 2: Resolving references..." -ForegroundColor Yellow
pdflatex -interaction=nonstopmode main.tex | Out-Null
Write-Host "✓ Pass 2 complete" -ForegroundColor Green

Write-Host "Pass 3: Final compilation..." -ForegroundColor Yellow
pdflatex -interaction=nonstopmode main.tex | Out-Null
Write-Host "✓ Pass 3 complete" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Compilation Complete!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PDF was generated
if (Test-Path "main.pdf") {
    $fileSize = (Get-Item "main.pdf").Length / 1MB
    Write-Host "✓ PDF generated successfully!" -ForegroundColor Green
    Write-Host "  File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
    Write-Host "  Location: $(Get-Location)\main.pdf" -ForegroundColor White
} else {
    Write-Host "✗ PDF generation failed. Check main.log for errors." -ForegroundColor Red
}

Write-Host ""
Write-Host "To view the PDF, run: start main.pdf" -ForegroundColor Cyan
Write-Host ""
