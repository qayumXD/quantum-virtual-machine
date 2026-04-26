# 🚀 Quick Commands Reference

**For:** QVM FYP LaTeX Documentation  
**Last Updated:** April 21, 2026

---

## 📝 LaTeX Compilation

### Compile Full Document
```bash
cd docs/fyp_latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Quick Compile (with latexmk)
```bash
cd docs/fyp_latex
latexmk -pdf main.tex
```

### Clean Build Files
```bash
cd docs/fyp_latex
latexmk -c  # Clean auxiliary files
latexmk -C  # Clean all including PDF
```

---

## 🎨 PlantUML Diagrams

### Generate Single Diagram
```bash
java -jar plantuml.jar path/to/diagram.puml
```

### Generate All Diagrams in Folder
```bash
java -jar plantuml.jar docs/diagrams/*.puml
```

### Generate with Output Directory
```bash
java -jar plantuml.jar -o ../output path/to/diagram.puml
```

---

## 💾 Backup Commands

### Windows (PowerShell)
```powershell
.\docs\backup_latex.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x docs/backup_latex.sh
./docs/backup_latex.sh
```

### Manual Backup
```bash
# Create timestamped backup
cp -r docs/fyp_latex backups/fyp_latex_$(date +%Y%m%d_%H%M%S)
```

---

## 🔍 Git Commands

### Check Status
```bash
git status
```

### Commit Changes
```bash
git add docs/fyp_latex/*.tex
git add docs/*.md
git commit -m "Your commit message"
```

### Push to Remote
```bash
git push origin main
```

### View History
```bash
git log --oneline --graph
```

---

## 📊 Progress Tracking

### View Current Status
```bash
cat docs/CURRENT_STATUS.md
```

### View Execution Plan
```bash
cat docs/fyp_latex_execution_plan.md
```

### View Phase 1 Progress
```bash
cat docs/phase1_progress.md
```

---

## 🧪 Testing Commands

### Test PlantUML
```bash
java -jar plantuml.jar docs/test_plantuml.puml
```

### Test LaTeX
```bash
cd docs
pdflatex test_latex.tex
```

### Run Python Tests (for code validation)
```bash
python -m pytest tests/
```

---

## 📁 File Locations

### LaTeX Files
```
docs/fyp_latex/
├── main.tex              # Main document
├── ch_1_introduction.tex # Chapter 1 ✅
├── ch_2_problem_definition.tex
├── ch_3_requirements.tex
├── ch_4_SDD.tex
├── ch_5_implementation.tex
├── ch_6_testing.tex
├── ch_7_conclusion.tex   # Chapter 7 ✅
└── Figures/              # Diagrams go here
```

### Planning Documents
```
docs/
├── fyp_latex_execution_plan.md      # Master plan
├── fyp_latex_preparation_analysis.md # Gap analysis
├── phase1_progress.md                # Progress tracking
├── CURRENT_STATUS.md                 # Quick status
├── TOOL_TESTING_CHECKLIST.md        # Testing guide
└── QUICK_COMMANDS.md                 # This file
```

---

## 🎯 Common Workflows

### After Writing a Chapter
```bash
# 1. Compile to check
cd docs/fyp_latex
pdflatex main.tex

# 2. Create backup
cd ../..
.\docs\backup_latex.ps1  # Windows
# or
./docs/backup_latex.sh   # Linux/Mac

# 3. Commit to Git
git add docs/fyp_latex/*.tex
git commit -m "Complete Chapter X"
git push
```

### Before Starting New Work
```bash
# 1. Check current status
cat docs/CURRENT_STATUS.md

# 2. Pull latest changes (if using Git)
git pull

# 3. Create backup
.\docs\backup_latex.ps1  # Windows
```

### When Stuck
```bash
# 1. Check execution plan
cat docs/fyp_latex_execution_plan.md

# 2. Check what's done
cat docs/phase1_progress.md

# 3. Check LaTeX logs
cat docs/fyp_latex/main.log
```

---

## 🔧 Troubleshooting

### LaTeX Won't Compile
```bash
# Check for errors
cd docs/fyp_latex
pdflatex main.tex | grep -i error

# Clean and rebuild
latexmk -C
latexmk -pdf main.tex
```

### PlantUML Not Working
```bash
# Check Java
java -version

# Test PlantUML
java -jar plantuml.jar -testdot

# Try with full path
java -jar /full/path/to/plantuml.jar diagram.puml
```

### Git Issues
```bash
# Discard local changes
git checkout -- file.tex

# View differences
git diff file.tex

# Stash changes
git stash
git stash pop
```

---

## 📞 Quick Help

### LaTeX Errors
- **Missing package:** `tlmgr install package-name`
- **Undefined control sequence:** Check for typos in commands
- **Missing figure:** Check file path and extension

### PlantUML Errors
- **Java not found:** Install Java JRE
- **Syntax error:** Check PlantUML syntax online
- **File not found:** Check file path

### Git Errors
- **Merge conflict:** Resolve manually, then `git add` and `git commit`
- **Push rejected:** `git pull` first, then `git push`

---

## 🎓 Useful Links

- **Overleaf:** https://www.overleaf.com
- **PlantUML:** https://plantuml.com
- **LaTeX Documentation:** https://www.latex-project.org/help/documentation/
- **Git Documentation:** https://git-scm.com/doc

---

**Quick Reference Created:** April 21, 2026  
**Keep this file handy for fast access to common commands!**
