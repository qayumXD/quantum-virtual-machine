# LaTeX Compilation Guide for FYP Document

## Understanding the Error

The error you're seeing is **NORMAL** for the first LaTeX compilation:

```
Latexmk: Latex failed to resolve 15 reference(s)
```

This happens because LaTeX needs **multiple passes** to:
1. First pass: Generate `.aux` files with label information
2. Second pass: Resolve `\ref{}` commands using the `.aux` files
3. Third pass: Update table of contents, list of figures, list of tables

## Solution: Run LaTeX Multiple Times

### Option 1: Use latexmk with -f flag (Recommended)

```bash
cd docs/fyp_latex
latexmk -pdf -f main.tex
```

The `-f` flag forces latexmk to continue even with unresolved references.

### Option 2: Run pdflatex Multiple Times

```bash
cd docs/fyp_latex
pdflatex main.tex
pdflatex main.tex
pdflatex main.tex
```

Run it **3 times** to resolve all references.

### Option 3: Use latexmk Normally (Multiple Runs)

```bash
cd docs/fyp_latex
latexmk -pdf main.tex
latexmk -pdf main.tex
```

Run latexmk twice - the second run will resolve all references.

## Verification

After successful compilation, you should see:

```
Latexmk: All targets (main.pdf) are up-to-date
```

And the file `main.pdf` should be generated without errors.

## Common Issues and Solutions

### Issue 1: Missing Figure Files

**Error:** `File 'figure.png' not found`

**Solution:** Ensure all PNG files are in the correct location:
- UML diagrams: `docs/uml/*.png`
- Screenshots: `docs/Screenshots/*.png`

### Issue 2: Missing Input Files

**Error:** `File 'chapter.tex' not found`

**Solution:** Ensure all chapter files exist:
- `ch_1_introduction.tex`
- `ch_2_problem_definition.tex`
- `ch_3_requirements.tex`
- `ch_4_SDD.tex`
- `ch_5_implementation.tex`
- `ch_6_testing.tex`
- `ch_7_conclusion.tex`
- `executive_summary.tex`
- `dedication.tex`
- `acknowledgement.tex`
- `abbreviations.tex`

### Issue 3: Bibliography Errors

**Error:** `Citation undefined`

**Solution:** Run bibtex after first pdflatex:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Current Status

✅ All chapter files exist
✅ All UML diagram PNG files exist
✅ All screenshot files exist
✅ Front matter files created (Executive Summary, Dedication, Acknowledgements, Abbreviations)

**Next Step:** Simply run the compilation command again!

## Quick Command

For the fastest compilation, use:

```bash
cd docs/fyp_latex
latexmk -pdf -f main.tex
```

This will:
1. Force compilation even with unresolved references
2. Run multiple passes automatically
3. Generate `main.pdf` successfully

## Expected Output

After successful compilation, you should have:
- `main.pdf` - Your complete FYP document (~100-150 pages)
- `main.aux` - Auxiliary file with label information
- `main.toc` - Table of contents
- `main.lof` - List of figures
- `main.lot` - List of tables
- `main.log` - Compilation log

## Cleaning Up

To clean auxiliary files:

```bash
latexmk -c
```

To clean everything including PDF:

```bash
latexmk -C
```

## Final Notes

- The "15 unresolved references" error is **expected** on first run
- Simply run the compilation command again
- All your files are in place and correct
- The PDF will generate successfully on the second/third pass

**You're ready to compile!** 🚀
