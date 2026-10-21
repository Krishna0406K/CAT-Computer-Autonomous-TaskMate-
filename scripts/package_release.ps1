Write-Host "=========================================="
Write-Host "   CAT Production Packager & Bundler      "
Write-Host "=========================================="

# 1. Run final validation
Write-Host "`n[1/3] Running System Validation..."
python scripts\validate_system.py

# 2. Build React UI
Write-Host "`n[2/3] Building React Frontend..."
cd apps\desktop
npm run build
cd ..\..

# 3. Build Tauri Bundler
Write-Host "`n[3/3] Compiling Tauri Native Release..."
cd apps\desktop
npm run tauri build

Write-Host "`n=========================================="
Write-Host "Packaging Complete!"
Write-Host "Your .msi and .exe installers are located in apps/desktop/src-tauri/target/release/bundle/"
