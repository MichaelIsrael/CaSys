# BUGS:
  - [x] Video files for old devices are never removed.
  - [x] Time used is one hour old (Maybe because of DST) [Using localtime() instead of gmtime()]
  - [x] Forever growing log file.
  - [ ] Exception is raised when the videos folder does not exist (should create it).
  - [ ] Unstable mail logging.
  - [x] SMTPHandler raises a Unicode exception. (Need to define a different handler by inheriting and adding encoding)

# General:
  - [x] Write copyright disssclaimer.
  - [x] Parse arguments.
  - [?] Delete old video files automatically (Based on name).
  - [x] Delete old video files automatically (Based on file creation time) Concerning Bug1.
  - [?] GLib-loop.
  - [ ] catching all interrupts.
  - [ ] Installation script.
  - [ ] Localization.

# Logging and reporting:
  - [x] Init logger.
  - [x] Use RotatingFileHandler.
  - [x] Email on Fatals. (SMTPHandler)
  - [x] Use a QueueHandler and a QueueListener for emails.
  - [x] Gstreamer bus for logging.

# Video capturing:
  - [x] Automatic video devices detect. /dev/video$Name
  - [x] Creating a different pipeline for each detected device.
  - [x] Build video objects with iterators.
  - [x] Gstreamer pipelines to files.
  - [?] Timer and chunking files.
  - [ ] Hot-pluging new cameras on the fly.

# Streaming:
  - [ ] RTSP Streaming. 
  - [ ] RTSP with authentication.
  - [ ] Hot-pluging streaming bin.
  - [ ] Stream viewer (client).

# System:
  - [ ] udev rule for known cameras.
  - [ ] startx/xinit script.
  - [ ] create user with relavent permissions.

# Interface:
  - [x] Basic interface to view cameras on a display.
  - [x] Divided display for four cameras.
  - [?] Display generic number of cameras.

# Control:
  - [ ] Control server.
  - [ ] Control client.
