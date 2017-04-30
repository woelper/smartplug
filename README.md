# Smartplug

Do stuff when a removable storage medium is inserted.

This software enables you to run actions on per-file or per-disk basis when a removable drive is added to the system. Optionally you may filter by file extension or storage name/label. While written with movie/video production in mind, you might use this for other stuff too (see below)

Some possible use cases:

- Create an index whenever a medium is inserted.
- Scan a medium for malicious files.
- Create proxy video files for every mov on the medium
- Backup all txt files on HOMEWORK medium to dropbox

Features:

- Designed to be cross-platform (Windows, MacOS, Linux)
- Flexible configuration format: Filter drives by ID, label and run any command line action on it or specific files
- Cooldown: Prevents running an action multiple times in a configurable time period
- Detects hotplugging of drives (add/remove drives at any time)

Roadmap:

- Add Gui support (web based)
- Add more fault tolerance (feedback welcome)
- Add binary releases for Windows / App bundle for MacOS

If you like this, have urgent feature requests or use it commercially, please consider becoming a patreon:
https://www.patreon.com/woelper
