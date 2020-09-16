# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Font rendering on high resolution displays on macOS.

## [0.6.1] - 2020-09-03
### Fixed
 - Application crash when remote services unavailable.
 - Ability to switch between Colab and JupyterLab flavours.
### Changed
 - Reset application settings on install.
 - Run container as host user on Linux (ensures correct file permissions).
### Removed
 - Unite Colab and JupyterLab application flavours.

## [0.6.0] - 2020-07-30
### Added
 - Improved logging.
 - Support for those unable to access Google Colabs.

## [0.4.5] - 2020-06-10
### Fixed
 - Container Update failure in macOS and Windows packages.
### Added
 - Provide a windows installer (not a single executable).
 - Communicate meta information to container.

## [0.4.3] - 2020-05-27
### Fixed
 - Ping system.
 - Read paginated responses from dockerhub.
 - Some awkward statefulness of buttons.
### Added
 - Add extra aux port.

## [0.4.2] - 2020-05-11
### Fixed
 - New tag due to corrupted CI push.

## [0.4.1] - 2020-05-11
### Fixed
 - pyinstaller builds on Ubuntu.
### Changed
 - Use QRunnable and other best practices.
### Added
 - Start building on windows.

## [0.4.0] - 2020-05-06
### Changed
 - Completely rewritten in Qt for better macOS compatibility

## [0.3.3] - 2020-04-29
### Fixed
 - First time container download issue.
### Added
 - Version information to home screen.
 - Additional update popup.

## [0.3.2] - 2020-04-28
### Added
 - Tracking statistics.

## [0.3.1] - 2020-04-21
### Fixed
 - Incorrect links in README and app.

## [0.3.0] - 2020-04-21

## [0.2.2] - 2020-04-20

## [0.2.1] - 2020-04-16
### Fixed
 - Desktop app shortcut after typo changes.

## [0.2.0] - 2020-04-16
### Fixed
 - Packaging bugs.
### Added
 - Download progress bar.
 - Provide feedback when docker not available.
 - Checking of input fields.
 - Help descriptions of required data.

## [0.1.8] - 2020-03-24
### Fixed
 - Update button.

## [0.1.7] - 2020-03-23
### Fixed
 - Issue where CI builds did not correctly include all graphics components.

## [0.1.6] - 2020-03-18
### Added
 - Filebrowser for datamount.

## [0.1.5] - 2020-03-13
