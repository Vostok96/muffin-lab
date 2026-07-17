$ErrorActionPreference = "Stop"

git branch -M main

if (git remote | Select-String -SimpleMatch "origin") {
    git remote set-url origin https://github.com/Vostok96/simcore.git
} else {
    git remote add origin https://github.com/Vostok96/simcore.git
}

git push -u origin main
