## Version 0.1

- [ ] Handle no album art being available.
	- [x] When no song is playing.
	- [ ] When the file is missing.
- [ ] Keybinds for:
	- [ ] Forcing album art refresh.
- [x] Add support for password authentication.
- [ ] Add ability to change settings:
	- [x] Through command line arguments,
	- [ ] Through a config file.
- [ ] Better logging.
- [x] Implement main functionality:
	- [x] Create window with `tkinter`,
	- [x] Get album art from MPD,
	- [x] Display album art,
	- [x] Use MPDs `idle` command to detect player and playlist changes
	and get new album art.
