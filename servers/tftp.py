import threading
from pkg.tftpy.tftpy import TftpServer

class TftpServerThreaded(object):
    def __init__(self, path):
        self.ip = '0.0.0.0'
        self.folder = path
        self.server = TftpServer(self.folder)
        self.thread = threading.Thread(target=self._run, args=())
        self.thread.daemon = True

    def _run(self):
        self.server.listen('0.0.0.0', 69)

    def start(self):
        self.thread.start()
    def stop(self):
        self.thread._stop()