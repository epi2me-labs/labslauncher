"""Labslauncher main application."""
import configparser
import functools
import os
import platform
import socket
import sys
import webbrowser

from epi2melabs import ping
from password_strength import PasswordPolicy
from pkg_resources import resource_filename
from PyQt5.QtCore import (
    PYQT_VERSION_STR, pyqtSignal as Signal, pyqtSlot as Slot,
    Qt, QT_VERSION_STR, QThreadPool, QTimer)
from PyQt5.QtGui import QIcon, QIntValidator, QPixmap
from PyQt5.QtWidgets import (
    QAction, QApplication, QDesktopWidget, QDialog, QFileDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

import labslauncher
from labslauncher.dockerutil import DockerClient
from labslauncher.qtext import ClickLabel, Settings, Worker


class Screen(QWidget):
    """Widgets to add to QStackedWidget which know the root."""

    @property
    def app(self):
        """Return the LabsLauncher instance."""
        p = self
        while not isinstance(p, LabsLauncher):
            p = p.parent()
        return p


class HomeScreen(Screen):
    """The application home screen."""

    goto_start = Signal()

    def __init__(self, parent=None):
        """Initialize the home screen."""
        super().__init__(parent=parent)
        self.layout = QVBoxLayout()
        self.cb = QApplication.clipboard()
        # Logo Image
        self.logo = QLabel()
        self.logo.setPixmap(
            QPixmap(resource_filename(
                'labslauncher', 'epi2me_labs_logo.png')
            ))
        self.logo.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo)
        self.layout.addStretch(-1)

        # Start/stop buttons
        self.l0 = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.goto_start.emit)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.on_stop)
        self.l0.addWidget(self.start_btn)
        self.l0.addWidget(self.stop_btn)
        self.layout.addLayout(self.l0)

        # status and address
        self.status_lbl = QLabel()
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_lbl)
        self.address_lbl = ClickLabel()
        self.address_lbl.clicked.connect(self.copy_address)
        self.address_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.address_lbl)
        self.layout.addStretch(-1)

        # welcome, version labels
        self.welcome_lbl = QLabel(
            "Navigate to the <a href={}>Welcome page</a> "
            "to get started.".format(self.app.settings["colab_link"]))
        self.welcome_lbl.setOpenExternalLinks(True)
        self.welcome_lbl.setAlignment(Qt.AlignCenter)
        self.version_lbl = QLabel()
        self.version_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome_lbl)
        self.layout.addWidget(self.version_lbl)
        self.setLayout(self.layout)

        # add callbacks
        self.app.docker.status.changed.connect(self.on_status)
        self.app.docker.tag.changed.connect(self.on_tag)
        self.on_status(self.app.docker.status.value)
        self.on_tag(self.app.docker.tag.value)

    def copy_address(self):
        """Copy server address to clipboard."""
        self.cb.clear(mode=self.cb.Clipboard)
        self.cb.setText(self.address_lbl.text(), mode=self.cb.Clipboard)
        msg = QMessageBox()
        msg.setText("Address copied")
        msg.setInformativeText(
            "The server address has been copied to the clipboard. "
            "It can be used in the Google Colab interface to connect "
            "to the notebook server.")
        msg.setWindowTitle("Address Copied")
        msg.exec_()

    def on_stop(self):
        """Stop and remove the container."""
        self.app.docker.clear_container()

    @Slot(str)
    def on_tag(self, value):
        """Set the version label."""
        self.version_lbl.setText(
            "Launcher version: {}    Server Version: {}".format(
                self.app.version, value))

    @Slot(object)
    def on_status(self, status):
        """Set state when container status changes."""
        old, new = status
        start_text = "Restart"
        stop_text = "Stop"
        extra_msg = ""
        if new in ("created", "exited"):
            color = "Crimson"
            stop_text = "Clear"
            extra_msg = "<br>(try restarting)"
        elif new == "unknown":
            color = "Orange"
            extra_msg = "<br>(waiting for docker)"
        elif new == "running":
            color = "DarkGreen"
        else:
            color = "MediumTurquoise"
            start_text = "Start"
        self.start_btn.setText(start_text)
        self.start_btn.setEnabled(new != "unknown")
        self.stop_btn.setText(stop_text)
        self.stop_btn.setEnabled(
            new not in ("inactive", "unknown"))
        self.status_lbl.setText(
            'Server status: <b><font color="{}">{}</font></b>{}'.format(
                color, new, extra_msg))

        address = ""
        self.address_lbl.setClickable(False)
        container = self.app.docker.container
        if container is not None and new == 'running':
            cargs = container.__dict__['attrs']['Args']
            for c in cargs:
                if c.startswith('--port='):
                    port = int(c.split('=')[1])
                elif c.startswith('--NotebookApp.token='):
                    token = c.split('=')[1]
            self.address_lbl.setClickable(True)
            address = "http://localhost:{}?token={}".format(port, token)
        self.address_lbl.setText(address)
        self.repaint()


class StartScreen(Screen):
    """Screen to set options and start server."""

    goto_home = Signal()
    path_help = (
        "The data path is the location on your computer you\n"
        "wish to be readable (and writeable) within the notebook\n"
        "environment. It will be available in the environment under\n"
        "`/epi2melabs`.")
    token_help = (
        "A secret token used to connect to the notebook server. Anyone\n"
        "with this token will be able to connect to the server, and \n"
        "therefore modify files under the data location. We recommend\n"
        "changing this from the default value.")
    port_help = (
        "The network port to used to communicate between web-browser\n"
        "and notebook server.")
    aux_port_help = (
        "An auxialiary network port used for secondary applications\n"
        "e.g. for use by the Pavian metagenomics dataset explorer.")

    def __init__(self, parent=None):
        """Initialize the screen."""
        super().__init__(parent=parent)
        self.token_policy = PasswordPolicy.from_names(
            length=8, uppercase=1, numbers=1)
        self.onlyInt = QIntValidator()
        self.layout = QVBoxLayout()

        # header
        self.l0 = QHBoxLayout()
        self.header_lbl = QLabel("Start server")
        self.l0.addWidget(self.header_lbl)
        self.layout.addLayout(self.l0)

        # data path, token, port
        self.l1 = QGridLayout()
        self.path_btn = QPushButton('Select folder')
        self.path_btn.clicked.connect(self.select_path)
        self.path_txt = QLineEdit(text=self.app.settings['data_mount'])
        self.path_txt.setToolTip(self.path_help)
        self.path_txt.setReadOnly(True)
        self.l1.addWidget(self.path_btn, 0, 0)
        self.l1.addWidget(self.path_txt, 0, 1)

        self.token_lbl = QLabel('Token:')
        self.token_txt = QLineEdit(text=self.app.settings['token'])
        self.token_txt.setMaxLength(16)
        self.token_txt.setToolTip(self.token_help)
        self.port_lbl = QLabel('Port:')
        self.port_txt = QLineEdit(text=str(self.app.settings['port']))
        self.port_txt.setValidator(self.onlyInt)
        self.port_txt.setToolTip(self.port_help)
        self.aux_port_lbl = QLabel('Aux. Port:')
        self.aux_port_txt = QLineEdit(text=str(self.app.settings['aux_port']))
        self.aux_port_txt.setValidator(self.onlyInt)
        self.aux_port_txt.setToolTip(self.aux_port_help)

        self.l1.addWidget(self.token_lbl, 1, 0)
        self.l1.addWidget(self.token_txt, 1, 1)
        self.l1.addWidget(self.port_lbl, 2, 0)
        self.l1.addWidget(self.port_txt, 2, 1)
        self.l1.addWidget(self.aux_port_lbl, 3, 0)
        self.l1.addWidget(self.aux_port_txt, 3, 1)
        self.layout.addLayout(self.l1)

        # spacer
        self.layout.insertStretch(-1)

        # start, update, back
        self.l3 = QHBoxLayout()
        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(self.validate_and_start)
        self.update_btn = QPushButton('Update')
        self.update_btn.clicked.connect(self.pull_image)
        self.back_btn = QPushButton('Back')
        self.back_btn.clicked.connect(self.goto_home.emit)

        self.l3.addWidget(self.start_btn)
        self.l3.addWidget(self.update_btn)
        self.l3.addWidget(self.back_btn)
        self.layout.addLayout(self.l3)

        self.setLayout(self.layout)

        self.app.docker.status.changed.connect(self.on_status)
        self.on_status(self.app.docker.status.value)

    def select_path(self):
        """Open data path dialog and set state."""
        starting_dir = self.path_txt.text()
        path = QFileDialog.getExistingDirectory(
            None, 'Open working directory', starting_dir,
            QFileDialog.ShowDirsOnly)
        if path != "":  # did not press cancel
            self.path_txt.setText(path)
            self.app.settings["data_mount"] = path

    def validate_and_start(self):
        """Start the container."""
        mount = self.path_txt.text()
        token = self.token_txt.text()
        port = self.port_txt.text()
        aux_port = self.aux_port_txt.text()
        # validate inputs
        valid = all([
            mount != "",
            os.path.isdir(mount),
            len(self.token_policy.test(token)) == 0,
            self.port_txt.hasAcceptableInput() and int(port) > 1024,
            self.aux_port_txt.hasAcceptableInput() and int(aux_port) > 1024,
            port != aux_port])

        if valid:
            if self.app.docker.latest_available_tag is None:
                self.pull_image(callback=self._start_container)
            else:
                self._start_container()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Input error")
            msg.setInformativeText("The inputs given are invalid.")
            msg.setWindowTitle("Input error")
            msg.setDetailedText(
                "1. A valid folder must be given.\n"
                "2. The token must be 8 characters and include uppercase, "
                "lowercase and numbers.\n"
                "3. The ports must be >1024.\n"
                "4. Port and Aux. port must be distinct.")
            msg.exec_()

    def _start_container(self):
        """Start container."""
        mount = self.path_txt.text()
        token = self.token_txt.text()
        port = self.port_txt.text()
        aux_port = self.aux_port_txt.text()

        for btn in (self.start_btn, self.update_btn):
            btn.setEnabled(False)
        self.app.docker.start_container(mount, token, port, aux_port)
        self.repaint()

        if self.app.docker.status.value[1] != "running":
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Server start error")
            msg.setInformativeText("An error occurred starting the server.")
            msg.setWindowTitle("Server Error")
            msg.setDetailedText(self.app.docker.last_failure)
            msg.exec_()
        else:
            config = configparser.ConfigParser()
            config['Host'] = {
                'hostname': socket.gethostname(),
                'operating_system': platform.platform()}
            config['Container'] = {
                'mount': mount, 'port': port, 'aux_port': aux_port,
                'image_tag': self.app.docker.latest_available_tag,
                'latest_tag': self.app.docker.latest_tag,
                'id': self.app.docker.container.id}
            config['Pings'] = {'enabled': self.settings["send_pings"]}
            fname = os.path.join(mount, os.path.basename(ping.CONTAINER_META))
            with open(fname, 'w') as config_file:
                config.write(config_file)

    def pull_image(self, *args, callback=None):
        """Pull new image in a thread.

        :param callback: function to run when pull as completed.
        """
        self.worker = Worker(self.app.docker.pull_image)
        self.worker.setAutoDelete(True)
        self.app.closing.connect(self.worker.stop)

        self.worker.signals.finished.connect(
            lambda: self.update_btn.setEnabled(
                self.app.docker.update_available))

        if callback is not None:
            self.worker.signals.finished.connect(callback)
        self.progress_dlg = DownloadDialog(
            progress=self.worker.signals.progress, parent=self)
        self.progress_dlg.finished.connect(self.worker.stop)
        self.worker.signals.finished.connect(self.progress_dlg.close)

        self.app.pool.start(self.worker)
        self.progress_dlg.show()

    @Slot(float)
    def on_download(self, value):
        """Set state when download progress changes."""
        self.header_lbl.setText(
            "Start server: (downloading - {:.1f}%)".format(value))

    @Slot(object)
    def on_status(self, status):
        """Set state when container status changes."""
        old, new = status
        msg = ""
        start_text = "Start"
        if new == "inactive":
            pass
        elif new in ("created", "exited"):
            msg = " (last attempt failed)"
            start_text = "Restart"
        elif new == "running":
            start_text = "Restart"
            self.app.show_home()

        self.start_btn.setText(start_text)
        self.start_btn.setEnabled(new != "unknown")
        self.header_lbl.setText('Start server: {}'.format(msg))
        self.update_btn.setEnabled(
            self.app.docker.update_available and new != "unknown")
        self.repaint()


class DownloadDialog(QDialog):
    """About dialog."""

    def __init__(self, progress, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.setWindowTitle("Downloading server.")
        self.layout = QVBoxLayout()
        self.lbl = QLabel("Downloading server components")
        self.layout.addWidget(self.lbl)
        self.pbar = QProgressBar(self)
        self.layout.addWidget(self.pbar)
        self.setLayout(self.layout)
        progress.connect(self.on_progress)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)
        self.setModal(True)
        self.resize(300, 50)

    @Slot(float)
    def on_progress(self, value):
        """Update progress bar.

        :param value: download progress.
        """
        self.pbar.setValue(value)

        extra = ""
        size = self.parent().app.docker.total_size
        if size is not None:
            size = size / 1024 / 1024 / 1024
            extra = "({:.1f}Gb)".format(size)
        self.lbl.setText("Downloading server components {}".format(extra))


class UpdateScreen(Screen):
    """Screen to display message that image update is available."""

    goto_start = Signal()
    update_text = (
        "<b>Update available</b><br>"
        "An update to the notebook server is available. Updating the "
        "notebook server will allowed continued use to the most recent "
        "EPI2ME Labs notebooks on GitHub. Please press the Update "
        "button on the main screen to update.<br><br>"
        "Current version: {}.<br>"
        "Latest version: {}.")

    def __init__(self, parent=None):
        """Initialize the screen."""
        super().__init__(parent=parent)

        self.layout = QVBoxLayout()

        self.update_lbl = QLabel()
        self.layout.addWidget(self.update_lbl)
        self.layout.insertStretch(-1)

        self.l0 = QHBoxLayout()
        self.layout.insertStretch(-1)
        self.dismiss_btn = QPushButton("OK")
        self.dismiss_btn.clicked.connect(self.goto_start.emit)
        self.l0.addWidget(self.dismiss_btn)
        self.layout.addLayout(self.l0)

        self.setLayout(self.layout)


class LabsLauncher(QMainWindow):
    """Main application window."""

    closing = Signal(bool)

    def __init__(self, app):
        """Initialize the main window."""
        super().__init__()
        self.version = labslauncher.__version__
        self.about = About(self.version)

        self.setWindowTitle("EPI2ME Labs Launcher")
        # display in centre of screen and fixed size
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.setFixedSize(400, 400)

        self.settings = Settings(labslauncher.Defaults())
        self.settings.override()
        app.aboutToQuit.connect(self.settings.qsettings.sync)

        self.pool = QThreadPool()
        app.aboutToQuit.connect(self.pool.waitForDone)

        fixed_tag = self.settings["fixed_tag"]
        if fixed_tag == "":
            fixed_tag = None
        self.docker = DockerClient(
            self.settings["image_name"], self.settings["server_name"],
            self.settings["data_bind"], self.settings["container_cmd"],
            host_only=self.settings["docker_restrict"],
            fixed_tag=fixed_tag)

        self.ping_timer = QTimer(self)
        self.pinger = ping.Pingu()
        self.docker.status.changed.connect(self.on_status)
        self.on_status(self.docker.status.value, boot=True)

        self.layout = QVBoxLayout()

        self.file_menu = self.menuBar().addMenu("&File")
        self.exit_act = QAction("Exit", self)
        self.exit_act.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_act)
        self.help_menu = self.menuBar().addMenu("&Help")
        self.about_act = QAction('About', self)
        self.about_act.triggered.connect(self.about.show)
        self.help_menu.addAction(self.about_act)
        self.help_act = QAction("Help", self)
        self.help_act.triggered.connect(self.show_help)
        self.help_menu.addAction(self.help_act)

        self.stack = QStackedWidget()
        self.home = HomeScreen(parent=self)
        self.start = StartScreen(parent=self)
        self.update = UpdateScreen(parent=self)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.start)
        self.stack.addWidget(self.update)
        self.layout.addWidget(self.stack)

        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.home.goto_start.connect(self.show_start)
        self.start.goto_home.connect(self.show_home)
        self.update.goto_start.connect(
            functools.partial(self.stack.setCurrentIndex, 1))
        self.show_home()

    def closeEvent(self, event):
        """Emit closing signal on window close."""
        self.closing.emit(True)
        super().closeEvent(event)

    def show_help(self):
        """Open webbrowser with application help."""
        webbrowser.open(self.settings['colab_help'])

    def show_home(self):
        """Move to the home screen."""
        self.stack.setCurrentIndex(0)

    def show_start(self):
        """Move to the start screen."""
        self.start.update_btn.setEnabled(self.docker.update_available)
        if self.docker.update_available:
            cur = self.docker.latest_available_tag
            new = self.docker.latest_tag
            self.update.update_lbl.setText(
                self.update.update_text.format(cur, new))
            self.update.update_lbl.setWordWrap(True)
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(1)

    @Slot(object)
    def on_status(self, status, boot=False):
        """Respond to container status changes."""
        old, new = status
        if old == new:
            return
        elif new == "running":
            if self.settings["send_pings"]:
                self.ping('start')
                callback = functools.partial(self.ping, 'update')
                self.ping_timer.setInterval(1000*60*20)  # 20 minutes
                self.ping_timer.start()
                self.ping_timer.timeout.connect(callback)
        elif old == "running" and new == "inactive":
            if self.settings["send_pings"]:
                self.ping_timer.stop()
                self.ping('stop')
        elif new == "unknown":
            self.ping_timer.stop()  # might not be required
            msg = QMessageBox(self)
            msg.setWindowTitle("Docker error")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Docker Error")
            msg.setInformativeText(
                "The application cannot communicate with docker.\n"
                "Please ensure that docker is running\n")
            msg.exec_()
        elif old == "unknown" and not boot:
            msg = QMessageBox(self)
            msg.setWindowTitle("Docker connection")
            msg.setText("Docker connection")
            msg.setInformativeText(
                "Connection to docker established.")
            msg.exec_()

    def moveEvent(self, event):
        """Move the progress dialog when main window moves."""
        super().moveEvent(event)
        if hasattr(self, 'start') and hasattr(self.start, 'progress_dlg'):
            diff = event.pos() - event.oldPos()
            geo = self.start.progress_dlg.geometry()
            geo.moveTopLeft(geo.topLeft() + diff)
            self.start.progress_dlg.setGeometry(geo)

    def ping(self, state):
        """Send a status ping.

        :param state: the container state (start, update, stop).
        """
        if "unknown" in self.docker.status.value:
            # the app just started
            return
        stats = None
        if state == 'stop':
            stats = self.docker.final_stats
        else:
            stats = self.docker.container.stats(stream=False)
        self.pinger.send_container_ping(
            state, stats, self.docker.image_name)


class About(QDialog):
    """About dialog."""

    def __init__(self, version, parent=None):
        """Initialize the dialog.

        :param version: application version string.
        """
        super().__init__(parent)
        self.setWindowTitle("About")
        self.layout = QVBoxLayout()
        self.label = QLabel(
            "<b>EPI2ME Labs Launcher {}</b><br>"
            "Copyright Oxford Nanopore Technologies Limited 2020<br>"
            "Mozilla Public License Version 2.0<br><br>"
            "The program include PyQt5 licensed under the GNU GPL v3.<br>"
            "PyQt5 {}<br>Qt {}<br>"
            "".format(version, PYQT_VERSION_STR, QT_VERSION_STR))
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


def main():
    """Entry point to run application."""
    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile(resource_filename('labslauncher', 'epi2me.png'))
    app.setWindowIcon(app_icon)
    launcher = LabsLauncher(app)
    launcher.show()
    sys.exit(app.exec_())
