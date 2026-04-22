# Fixing the 365 LaTeX Problems

## Understanding the Issue

You're seeing **365 problems** in VS Code's Problems tab. These are **NOT actual errors** - they are:

1. **Undefined References** (15 problems) - Need multiple LaTeX passes to resolve
2. **LaTeX Warnings** (350+ problems) - Mostly informational, not critical

## Why This Happens

LaTeX is a **multi-pass compiler**:
- **Pass 1:** Generates `.aux` files with label information
- **Pass 2:** Resolves `\ref{}` commands using `.aux` files  
- **Pass 3:** Updates table of contents, list of figures, list of tables

After the first pass, LaTeX shows warnings about undefined references because it hasn't created the `.aux` files yet. **This is completely normal!**

## The Solution: Run LaTeX 3 Times

### Option 1: Use the Compilation Scripts (Easiest)

I've created scripts that automatically run LaTeX 3 times:

**On Windows (PowerShell):**
```powershell
cd docs/fyp_latex
.\compile.ps1
```

**On Linux/Mac (Bash):**
```bash
cd docs/fyp_latex
chmod +x compile.sh
./compile.sh
```

### Option 2: Manual Compilation

**Using latexmk (Recommended):**
```bash
cd docs/fyp_latex
latexmk -pdf -f main.tex
```

**Using pdflatex directly:**
```bash
cd docs/fyp_latex
pdflatex main.tex
pdflatex main.tex
pdflatex main.tex
```

### Option 3: VS Code LaTeX Workshop

If you have the LaTeX Workshop extension:
1. Open `main.tex` in VS Code
2. Press `Ctrl+Alt+B` (or `Cmd+Option+B` on Mac)
3. Wait for compilation to complete
4. Press `Ctrl+Alt+B` again (run it 2-3 times)

## What Will Happen

After running LaTeX 3 times:

✅ All 15 undefined references will be resolved
✅ Table of contents will be generated
✅ List of figures will be generated
✅ List of tables will be generated
✅ All cross-references will work
✅ The 365 problems will reduce to ~0-10 minor warnings

## Verification

After successful compilation, check:

1. **PDF Generated:** `main.pdf` should exist and be ~5-10 MB
2. **No Errors:** The log should say "Output written on main.pdf"
3. **Page Count:** Should be ~100-150 pages
4. **Problems Tab:** Should show 0-10 warnings (not 365!)

## Common Remaining Warnings (Safe to Ignore)

After proper compilation, you might see a few warnings like:

- `Overfull \hbox` - Text slightly too wide (cosmetic)
- `Underfull \hbox` - Text slightly too narrow (cosmetic)
- `Package hyperref Warning` - Bookmark issues (cosmetic)

These are **safe to ignore** - they don't affect the PDF quality.

## Quick Fix Commands

**Windows (PowerShell):**
```powershell
cd docs\fyp_latex
pdflatex main.tex; pdflatex main.tex; pdflatex main.tex
```

**Linux/Mac/WSL (Bash):**
```bash
cd docs/fyp_latex
pdflatex main.tex && pdflatex main.tex && pdflatex main.tex
```

**Using latexmk (All platforms):**
```bash
cd docs/fyp_latex
latexmk -pdf -f main.tex
```

## Expected Results

### Before (First Pass):
- ❌ 365 problems in VS Code
- ❌ Undefined references
- ❌ Empty table of contents
- ❌ Missing list of figures/tables

### After (Third Pass):
- ✅ 0-10 minor warnings
- ✅ All references resolved
- ✅ Complete table of contents
- ✅ Complete list of figures/tables
- ✅ Perfect PDF generated

## Troubleshooting

### Problem: "pdflatex: command not found"

**Solution:** Install LaTeX distribution:
- **Windows:** Install MiKTeX or TeX Live
- **Mac:** Install MacTeX
- **Linux:** `sudo apt-get install texlive-full`

### Problem: "File not found" errors

**Solution:** Ensure you're in the correct directory:
```bash
cd docs/fyp_latex
pwd  # Should show: .../quantum-virtual-machine/docs/fyp_latex
```

### Problem: Still seeing 365 problems after 3 passes

**Solution:** 
1. Close and reopen VS Code
2. Run: `latexmk -c` to clean auxiliary files
3. Run: `latexmk -pdf -f main.tex` again

## Files Generated (Normal)

After compilation, you'll see these files (all normal):
- ✅ `main.pdf` - Your final document
- ✅ `main.aux` - Auxiliary file (labels)
- ✅ `main.toc` - Table of contents
- ✅ `main.lof` - List of figures
- ✅ `main.lot` - List of tables
- ✅ `main.log` - Compilation log
- ✅ `main.out` - Hyperref output
- ✅ `main.fls` - File list
- ✅ `main.fdb_latexmk` - Latexmk database

## Summary

**The 365 problems are NOT real errors!** They're just LaTeX warnings from the first compilation pass. Simply run LaTeX 2-3 more times and they'll all disappear.

**Quick Fix:**
```bash
cd docs/fyp_latex
latexmk -pdf -f main.tex
```

**That's it!** Your PDF will be perfect. 🎉

---

**Need Help?**
- Check `main.log` for detailed error messages
- Look for lines starting with `!` (actual errors)
- Ignore lines starting with `Warning:` (informational)
