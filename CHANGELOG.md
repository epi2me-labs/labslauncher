# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
 - Monitoring and logging of docker container in GUI.

## [v1.0.4] - 2021-01-06
### Fixed
 - Added extra libraries required on Ubuntu after Qt upgrade
### Added
 - Application update notification on start.
 - Changelog dialog to help menu.

## [v1.0.3] - 2020-12-16
### Changed
 - Updated pyqt5 and pyqt5-sip for compatibility with MacOS Big Sur.
### Removed
 - Colab support in container run command
 - Enablement of cross-site support in container run command

## [v1.0.2]
### Added
 - HTTP and FTP proxy settings
 - Pass proxy settings to container environment variables

## [v1.0.1]
### Added
 - Ability to specify an https proxy
### Fixed
 - Application crash when running for a prolonged period after container stop

## [v1.0.0]
### Changed
 - Default docker image is now ontresearch/epi2melabs-notebook

## [v0.6.5]
### Changed
 - Blog URL for quickstart pages

## [v0.6.4]
### Fixed
 - Correct URL for opening JupyterLab

## [v0.6.3]
### Removed
 - Ability to change app behaviour for Colab
### Changed
 - Help links now point to EPI2MELabs blog site

## [v0.6.2]
### Fixed
 - Font rendering on high resolution displays on macOS.
### Changed
 - Default application flavour is now Jupyterab.

## [v0.6.1] - 2020-09-03
### Fixed
 - Application crash when remote services unavailable.
 - Ability to switch between Colab and JupyterLab flavours.
### Changed
 - Reset application settings on install.
 - Run container as host user on Linux (ensures correct file permissions).
### Removed
 - Unite Colab and JupyterLab application flavours.

## [v0.6.0] - 2020-07-30
### Added
 - Improved logging.
 - Support for those unable to access Google Colabs.

## [v0.4.5] - 2020-06-10
### Fixed
 - Container Update failure in macOS and Windows packages.
### Added
 - Provide a windows installer (not a single executable).
 - Communicate meta information to container.

## [v0.4.3] - 2020-05-27
### Fixed
 - Ping system.
 - Read paginated responses from dockerhub.
 - Some awkward statefulness of buttons.
### Added
 - Add extra aux port.

## [v0.4.2] - 2020-05-11
### Fixed
 - New tag due to corrupted CI push.

## [v0.4.1] - 2020-05-11
### Fixed
 - pyinstaller builds on Ubuntu.
### Changed
 - Use QRunnable and other best practices.
### Added
 - Start building on windows.

## [v0.4.0] - 2020-05-06
### Changed
 - Completely rewritten in Qt for better macOS compatibility

## [v0.3.3] - 2020-04-29
### Fixed
 - First time container download issue.
### Added
 - Version information to home screen.
 - Additional update popup.

## [v0.3.2] - 2020-04-28
### Added
 - Tracking statistics.

## [v0.3.1] - 2020-04-21
### Fixed
 - Incorrect links in README and app.

## [v0.3.0] - 2020-04-21

## [v0.2.2] - 2020-04-20

## [v0.2.1] - 2020-04-16
### Fixed
 - Desktop app shortcut after typo changes.

## [v0.2.0] - 2020-04-16
### Fixed
 - Packaging bugs.
### Added
 - Download progress bar.
 - Provide feedback when docker not available.
 - Checking of input fields.
 - Help descriptions of required data.

## [v0.1.8] - 2020-03-24
### Fixed
 - Update button.

## [v0.1.7] - 2020-03-23
### Fixed
 - Issue where CI builds did not correctly include all graphics components.

## [v0.1.6] - 2020-03-18
### Added
 - Filebrowser for datamount.

## [v0.1.5] - 2020-03-13
