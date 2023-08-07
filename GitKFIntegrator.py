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

mod_packages_in_path = "..\\..\\KFGame\\GitSrc\\CD-Combined-Edition"
mod_output_dir = "..\\..\\KFGame\\Unpublished\\BrewedPC\\Script"
mod_packages = ["CustomHUD", "CombinedCD2", "CombinedCDContent"]

class MyHandler(FileSystemEventHandler):
	log_mod_count = 0

	def on_modified(self, event):
		file_name = event.src_path.replace((log_dir + "\\"), "")
		print("[Modified]", file_name, sep="\t")
		if file_name == "Launch.log":
			self.log_mod_count += 1

	def on_created(self, event):
		file_name = event.src_path.replace((log_dir + "\\"), "")
		print("[Created]", file_name, sep="\t")

def get_mod_packages_section():
	line = "[ModPackages]\n"
	line += "ModPackagesInPath=" + mod_packages_in_path + "\n"
	line += "ModOutputDir=" + mod_output_dir + "\n"
	for i in range(len(mod_packages)):
		line += "ModPackages=" + mod_packages[i] + "\n"
	print("\n" + line)
	return line

def setup_editor_cfg():
	# Reading
	with open(kfeditor_cfg, 'r') as file:
		lines = file.readlines()

	# Modifying
	modified_lines = []
	section_stage = 0

	for line in lines:
		match(section_stage):
			# seeking, always append sth
			case 0:
				if line == "[ModPackages]\n":
					line = get_mod_packages_section()
					section_stage = 1
				modified_lines.append(line)
			# skipping to the next section
			case 1:
				if "[" in line:
					section_stage = 2
					modified_lines.append(line)
			# This case should stand for just appending left lines.
			case _:
				modified_lines.append(line)
	if section_stage == 0:
		modified_lines.append(get_mod_packages_section())

	# Writing
	with open(kfeditor_cfg, 'w') as file:
		file.writelines(modified_lines)

def get_log_info():
	with open (log_dir + "\\" + "Launch.log", 'r') as file:
		lines = file.readlines()

	results = ""
	section_stage = 0
	compile_state = -1
	for line in lines:
		match(section_stage):
			case 0:
				if "Executing Class UnrealEd.MakeCommandlet" in line:
					section_stage = 1
			case 1:
				match(compile_state):
					case -1:
						if "Scripts successfully compiled" in line:
							compile_state = 0
							line = line.split(" - ")[0] + "\n"
							results += line.replace("Log: ", "")
						elif "Compile aborted due to errors." in line:
							compile_state = 2
							results += line.replace("Log: ", "")
						elif "No scripts need recompiling." in line:
							compile_state = 0
							results += line.replace("Log: ", "")
					case 0:
						if "Warning/Error Summary" in line:
							compile_state = 1
							results += line.replace("Log: ", "")
						elif "Success - " in line:
							results += line.replace("Log: ", "")
							return {"log" : results, "state" : compile_state}
					case 1 | 2:
						if "Src\\" in line:
							line = line.split("Log")[0] + line.split("Src\\")[1]
						results += line.replace("Log: ", "")
						if "Success - " in line or "Failure - " in line:
							return {"log" : results, "state" : compile_state}
	return {"log" : results, "state" : -1}

if __name__ == "__main__":
	try:
		# init
		logging.basicConfig(level=logging.INFO,
    						format="[Log]\t%(message)s")
		subprocess.run("git --version")
		setup_editor_cfg()

		# compile with tracking
		event_handler = MyHandler() #LoggingEventHandler()
		observer = Observer()
		observer.schedule(event_handler, log_dir, recursive=False)
		observer.start()
		kfeditor = subprocess.Popen(kfeditor_dir + "/kfeditor make")
		try:
			i = 0
			logging.info("Compiling...")
			while event_handler.log_mod_count < 2:
				time.sleep(1)
			print("\n" + get_log_info()["log"])
			logging.info("state: " + str(get_log_info()["state"]))

		finally:
			observer.stop()
			observer.join()
			kfeditor.terminate()

	except:
		print("[ERROR]\tFatal Error!")
		sys.exit()