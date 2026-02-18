#!/bin/bash
# vending startup script

FONT_FILE="/home/admin/.local/share/fonts/Google/TrueType/Roboto_Regular.ttf"
if [ -f "$FILE" ]; then
    echo "Font $FILE exists"
else
    echo "Font $FILE does not exist"
    cp -r /home/admin/Desktop/client/GUI/assets/fonts /home/admin/.local/share/fonts
fi

cd /home/admin/Desktop/client
source venv/bin/activate
python3 main.py