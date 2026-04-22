#!/bin/bash
# LaTeX Compilation Script
# This script runs pdflatex multiple times to resolve all references

echo "========================================="
echo "FYP LaTeX Compilation Script"
echo "========================================="
echo ""

cd "$(dirname "$0")"

echo "Pass 1: Initial compilation..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
echo "✓ Pass 1 complete"

echo "Pass 2: Resolving references..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
echo "✓ Pass 2 complete"

echo "Pass 3: Final compilation..."
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
echo "✓ Pass 3 complete"

echo ""
echo "========================================="
echo "Compilation Complete!"
echo "========================================="
echo ""
echo "Output: main.pdf"
echo ""

# Check if PDF was generated
if [ -f "main.pdf" ]; then
    echo "✓ PDF generated successfully!"
    echo "  File size: $(du -h main.pdf | cut -f1)"
    echo "  Pages: $(pdfinfo main.pdf 2>/dev/null | grep Pages | awk '{print $2}')"
else
    echo "✗ PDF generation failed. Check main.log for errors."
fi

echo ""
