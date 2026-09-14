cd slot-osint

# .gitignore + README + .env.example ရှိပြီးသားဆိုရင်
git init -b main
git add .
git status                          # .env မပါဘူး သေချာစေ
git commit -m "Initial commit: slot OSINT dashboard"

# GitHub မှာ repo ဖန်တီးပြီးရင်
git remote add origin git@github.com:YOUR_USERNAME/slot-osint.git
git branch -M main
git push -u origin main