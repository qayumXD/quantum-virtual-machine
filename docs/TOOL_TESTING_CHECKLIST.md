# 🛠️ Tool Testing Checklist - Day 7

**Date:** April 21, 2026  
**Purpose:** Verify all tools work before Phase 2

---

## ✅ Testing Checklist

### 1. PlantUML Test
**Command:**
```bash
java -jar plantuml.jar docs/test_plantuml.puml
```

**Expected Result:**
- [ ] File `docs/test_plantuml.png` is created
- [ ] Image shows a sequence diagram with User → CLI → Parser → Simulator → Results
- [ ] No errors in terminal

**If it fails:**
- Check Java is installed: `java -version`
- Check plantuml.jar path is correct
- Try: `java -jar path/to/plantuml.jar docs/test_plantuml.puml`

---

### 2. Local LaTeX Test
**Command:**
```bash
cd docs
pdflatex test_latex.tex
```

**Expected Result:**
- [ ] File `docs/test_latex.pdf` is created
- [ ] PDF opens and shows "Test Chapter" with formatted text
- [ ] No compilation errors (warnings are OK)

**If it fails:**
- Check LaTeX is installed: `pdflatex --version`
- Check for missing packages
- Try: `tlmgr install <package-name>` for missing packages

---

### 3. Full FYP Template Compilation
**Command:**
```bash
cd docs/fyp_latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

**Or with latexmk:**
```bash
cd docs/fyp_latex
latexmk -pdf main.tex
```

**Expected Result:**
- [ ] File `docs/fyp_latex/main.pdf` is created
- [ ] PDF opens and shows complete FYP document
- [ ] Chapter 1 (Introduction) appears with all 6 sections
- [ ] Chapter 7 (Conclusion) appears with all 3 sections
- [ ] Table of Contents is generated
- [ ] No critical errors (warnings are OK)

**Common Issues:**
- Missing figures: OK for now (we'll add in Phase 2)
- Bibliography warnings: OK (we'll fix in Phase 4)
- Duplicate label warnings: OK (template issue, we'll fix)

---

### 4. Overleaf Upload
**Steps:**
1. [ ] Go to https://www.overleaf.com
2. [ ] Login to your account
3. [ ] Click "New Project" → "Upload Project"
4. [ ] Create ZIP of `docs/fyp_latex` folder
5. [ ] Upload the ZIP file
6. [ ] Wait for Overleaf to process
7. [ ] Click "Recompile" button
8. [ ] Verify PDF generates correctly

**Expected Result:**
- [ ] Project uploads successfully
- [ ] Compilation succeeds on Overleaf
- [ ] PDF preview shows Chapters 1 and 7 correctly
- [ ] Can edit files in Overleaf

**Overleaf Tips:**
- Use "Recompile" button to regenerate PDF
- Use "Logs and output files" to see errors
- Use "Download PDF" to save locally

---

### 5. Backup Strategy
**Windows (PowerShell):**
```powershell
.\docs\backup_latex.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x docs/backup_latex.sh
./docs/backup_latex.sh
```

**Expected Result:**
- [ ] Folder `backups/latex_backup_YYYYMMDD_HHMMSS` is created
- [ ] ZIP file `backups/latex_backup_YYYYMMDD_HHMMSS.zip` is created
- [ ] ZIP contains all LaTeX files and planning documents

**Backup Schedule:**
- After completing each chapter
- Before major changes
- Daily during intensive work periods
- Before submission

---

### 6. Git Commit (Optional but Recommended)
**Commands:**
```bash
git add docs/fyp_latex/ch_1_introduction.tex
git add docs/fyp_latex/ch_7_conclusion.tex
git add docs/*.md
git commit -m "Phase 1: Complete Chapter 7 and Chapter 1 (sections 1.1-1.6)"
git push
```

**Expected Result:**
- [ ] Changes committed to Git
- [ ] Changes pushed to GitHub (if using)
- [ ] Commit history shows progress

---

## 📊 Testing Summary

### All Tests Passed?
- [ ] PlantUML works ✅
- [ ] Local LaTeX works ✅
- [ ] Full template compiles ✅
- [ ] Overleaf upload successful ✅
- [ ] Backup script works ✅
- [ ] Git commit successful ✅

### If All Tests Pass:
✅ **READY TO PROCEED TO CHAPTER 2!**

### If Any Test Fails:
1. Check error messages carefully
2. Google the specific error
3. Check package installations
4. Try alternative tools (e.g., Draw.io instead of PlantUML)
5. Ask for help if stuck

---

## 🎯 After Testing

Once all tests pass, update the execution plan:

```markdown
### Day 7: Tool Setup & Verification (2 hours)
**Status:** COMPLETE ✅
**Tasks:**
- [x] Overleaf account setup ✅
- [x] Local LaTeX installation ✅
- [x] PlantUML .jar downloaded ✅
- [x] Test PlantUML with simple diagram ✅
- [x] Upload LaTeX template to Overleaf ✅
- [x] Test compilation ✅
- [x] Create backup strategy ✅
```

---

## 🚀 Next Steps

**After all tools are verified:**
1. ✅ Mark Day 7 as complete
2. ✅ Update Phase 1 progress to 100%
3. ✅ Celebrate! 🎉
4. ➡️ **START CHAPTER 2** (Day 5-6 tasks)

---

**Checklist Created:** April 21, 2026  
**Status:** Ready for testing  
**Estimated Time:** 1-2 hours
