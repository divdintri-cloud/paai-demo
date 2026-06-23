#!/bin/bash

cd ~/PAAI || exit 1

echo "Checking Python syntax..."
source .venv/bin/activate

python3 -m py_compile app.py
python3 -m py_compile skills/literacy_skills.py
python3 -m py_compile skills/grocery_skills.py
python3 -m py_compile skills/payment_skills.py
python3 -m py_compile skills/activity_log.py

if [ $? -ne 0 ]; then
  echo "Syntax check failed. Fix errors before releasing."
  exit 1
fi

echo "Git status:"
git status

echo ""
echo "If everything looks good, run:"
echo "git add app.py skills/ demo_data/ evals/ README.md requirements.txt"
echo "git commit -m \"Your release message here\""
echo "git pull --rebase origin master"
echo "git push origin master"
