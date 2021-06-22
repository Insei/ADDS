import threading
import time
import uvicorn

class UvicornServerThreaded(object):
    def __init__(self, app):
        self.app = app
        self.thread = threading.Thread(target=self._run, args=())
        self.thread.daemon = True                            # Daemonize thread
        #self.thread.start()                                  # Start the execution

    def _run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=5000)

    def start(self):
        self.thread.start()
    def stop(self):
        self.thread._stop()
    def join(self):
        self.thread.join()