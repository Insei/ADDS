import threading
import os, shutil
from pkg.tftpy.tftpy import TftpServer

class TftpDeploymentHelper(object):
    def __init__(self, tftp_root, images_dir):
        self.tftp_root = tftp_root
        self.images_dir = images_dir

    def mkdir(self, folder):
        if not os.path.exists(self.tftp_root + folder):
            os.mkdir(self.tftp_root + folder)

    def rmdir(self, folder):
        fullpath = self.tftp_root + folder
        if not os.path.exists(fullpath):
            return
        shutil.rmtree(fullpath)

    def make_bootloader(self, folder, model, bootloader="u-boot", type="normal", ipxe_url_str=""):
        self.rmdir(folder)
        tftp_device_root = os.path.join(self.tftp_root, folder)
        firmware_images_dir = os.path.join(self.images_dir, model, "firmware")
        bootloader_images_dir = os.path.join(self.images_dir, model, bootloader, type)
        shutil.copytree(firmware_images_dir, tftp_device_root)
        for bootloaderfile in os.listdir(bootloader_images_dir):
            bootloaderfilepath = os.path.join(bootloader_images_dir, bootloaderfile)
            shutil.copy(bootloaderfilepath, tftp_device_root)

        # we need ipxe for get call back that erease OK and we can power off device.
        if ipxe_url_str or type == "erase-sdcard":
            ipxe_images_dir = os.path.join(self.images_dir, "ipxe")
            shutil.copy(os.path.join(ipxe_images_dir, "arm64-ipxe.efi"), os.path.join(tftp_device_root, "ipxe.efi"))
            shutil.copy(os.path.join(ipxe_images_dir, "ipxe.efi.cfg"), tftp_device_root)

            ipxe_cfg_content = ""
            ipxe_cfg_file_path = os.path.join(tftp_device_root, "ipxe.efi.cfg")
            with open (ipxe_cfg_file_path, 'r') as ipxe_cfg_file:
                ipxe_cfg_content = ipxe_cfg_file.read()
            with open (ipxe_cfg_file_path, 'w') as ipxe_cfg_file:
                ipxe_cfg_file.write(ipxe_cfg_content.replace("REPLACEURL", ipxe_url_str))
                

        

class TftpServerThreaded(object):
    def __init__(self, path, images_path):
        self.ip = '0.0.0.0'
        self.folder = path
        self.images_folder=images_path
        self.server = TftpServer(self.folder)
        self.thread = threading.Thread(target=self._run, args=())
        self.thread.daemon = True
        self.helper = TftpDeploymentHelper(path, images_path)

    def _run(self):
        self.server.listen('0.0.0.0', 69)

    def start(self):
        self.thread.start()
    def stop(self):
        self.thread._stop()