import subprocess
import sys
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

game_dir = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\killingfloor2"
kfeditor_dir = game_dir + "\\Binaries\\Win64"

home_dir = "C:\\Users\\maima\\Documents\\My Games\\KillingFloor2"
kfeditor_cfg = home_dir + "\\KFGame\\Config\\KFEditor.ini"
log_dir = home_dir + "\\KFGame\\Logs"

class MyHandler(FileSystemEventHandler):
	log_mod_count = 0

	def on_modified(self, event):
		file_name = event.src_path.replace((log_dir + "\\"), "")
		print("[Modified]", file_name)
		if file_name == "Launch.log":
			self.log_mod_count += 1

	def on_created(self, event):
		file_name = event.src_path.replace((log_dir + "\\"), "")
		print("[Created]", file_name)

if __name__ == "__main__":
	try:
		# init
		logging.basicConfig(level=logging.INFO,
    						format="[Log] %(message)s")
		subprocess.run("git --version")

		# compile with tracking
		event_handler = MyHandler() #LoggingEventHandler()
		observer = Observer()
		observer.schedule(event_handler, log_dir, recursive=False)
		observer.start()
		subprocess.Popen(kfeditor_dir + "/kfeditor make")
		try:
			i = 0
			logging.info("Compiling...")
			while event_handler.log_mod_count < 2:
				time.sleep(1)
			logging.info("The second modifying is detected.")

		finally:
			observer.stop()
			observer.join()

	except:
		print("ERROR!")
		sys.exit()