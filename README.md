# Matrix-Barista-Bot
A port of the Python [Telegram-Response-Bot](https://github.com/Matthew-Klawitter/Telegram-Response-Bot) project to the matrix platform.

Current aim is to redesign under a more optimized and responsive architecture as well as to promote compatiblity with the prior plugin api. 

## Requirements
1. Python 3.7+
2. Python modules found in requirements.txt
3. (Optional) Olm for implementation of matrix encryption standards to connect to E2EE chatrooms.
4. (Optional) Recommended to upgrade the matrix-nio module to "matrix-nio[e2e]" if installing alongside Olm.

## Features
Currently features include:
1. MumbleAlerts - Periodic alerts that respond when the user count to a mumble server changes
2. RollPlugin - Simulate dice rolls by typing "!r #d#" where the first number is the number of dice, and the second the number of sides. Append "+#" or "-#" to apply a positive or negative modifier to each roll.
3. MCAlerts - Messages on user connect/disconnecting from a specified Minecraft server