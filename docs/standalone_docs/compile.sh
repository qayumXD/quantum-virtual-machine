#!/bin/bash
# Compilation script for standalone SRS and SDD documents
# Usage: ./compile.sh [srs|sdd|all]

set -e

TARGET="${1:-all}"

compile_doc() {
    local DOC="$1"
    local NAME="$2"
    echo "========================================="
    echo "Compiling $NAME..."
    echo "========================================="

    echo "Pass 1: Initial compilation..."
    pdflatex -interaction=nonstopmode "$DOC.tex" > /dev/null 2>&1
    echo "✓ Pass 1 complete"

    echo "Pass 2: Resolving references..."
    pdflatex -interaction=nonstopmode "$DOC.tex" > /dev/null 2>&1
    echo "✓ Pass 2 complete"

    echo "Pass 3: Final compilation..."
    pdflatex -interaction=nonstopmode "$DOC.tex" > /dev/null 2>&1
    echo "✓ Pass 3 complete"

    if [ -f "$DOC.pdf" ]; then
        SIZE=$(du -h "$DOC.pdf" | cut -f1)
        PAGES=$(pdfinfo "$DOC.pdf" 2>/dev/null | grep Pages | awk '{print $2}')
        echo ""
        echo "✓ $NAME generated successfully!"
        echo "  Output: $DOC.pdf"
        echo "  File size: $SIZE"
        echo "  Pages: $PAGES"
    else
        echo "✗ Error: $DOC.pdf was not generated"
        exit 1
    fi
    echo ""
}

case "$TARGET" in
    srs)
        compile_doc "SRS" "Software Requirements Specification"
        ;;
    sdd)
        compile_doc "SDD" "Software Design Document"
        ;;
    all)
        compile_doc "SRS" "Software Requirements Specification"
        compile_doc "SDD" "Software Design Document"
        echo "========================================="
        echo "All documents compiled successfully!"
        echo "========================================="
        ;;
    *)
        echo "Usage: $0 [srs|sdd|all]"
        exit 1
        ;;
esac
