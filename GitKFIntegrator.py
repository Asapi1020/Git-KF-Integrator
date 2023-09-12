import subprocess
import sys
import logging
import colorlog
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

steam_dir = "C:\\Program Files (x86)"
kfeditor_dir = steam_dir + "\\Steam\\steamapps\\common\\killingfloor2\\Binaries\\Win64"

home_dir = "C:\\Users\\maima\\Documents\\My Games\\KillingFloor2"
kfeditor_cfg = home_dir + "\\KFGame\\Config\\KFEditor.ini"
log_dir = home_dir + "\\KFGame\\Logs"

mod_packages_in_path = "C:\\Users\\maima\\Documents\\My Games\\KillingFloor2\\KFGame\\GitSrc\\CD-Combined-Edition"
mod_output_dir = "..\\..\\KFGame\\Unpublished\\BrewedPC\\Script"
mod_packages = ["CustomHUD", "CombinedCD2", "CombinedCDContent"]

language_for_cooking = "int"
map_name = "kf-subsynth"
game_mode = "CombinedCD2.CD_Survival"
mutators = ["FriendlyHUD.FriendlyHUDMutator"]
difficulty = 3
game_length = 2
other_opt = ""

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

def setup_logger():
	l = colorlog.getLogger()
	l.setLevel(logging.DEBUG)
	handler = colorlog.StreamHandler()
	handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(message)s'))
	l.addHandler(handler)
	return l

def gitprocess(cmd):
	subprocess.run("git " + cmd, cwd=mod_packages_in_path)

def get_mod_packages_section():
	line = "[ModPackages]\n"
	line += "ModPackagesInPath=" + mod_packages_in_path + "\n"
	line += "ModOutputDir=" + mod_output_dir + "\n"
	for i in range(len(mod_packages)):
		line += "ModPackages=" + mod_packages[i] + "\n"
	print(line)
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
							line = "<Warning>" + line.split("Log")[0] + line.split("Src\\")[1]
						results += line.replace("Log: ", "")
						if "Success - " in line or "Failure - " in line:
							return {"log" : results, "state" : compile_state}
	return {"log" : results, "state" : -1}

def output_log(log, logger):
	splitbuf = log.split("\n")
	for line in splitbuf:
		if "Success - " in line:
			logger.info(line)
		elif "<Warning>" in line:
			line = line.replace("<Warning>", "")
			if "Error, " in line:
				logger.error(line)
			else:
				logger.warning(line)
		elif "Failure - " in line:
			logger.error(line)
		else:
			logger.debug(line)

def setup_launch_cmd():
	cmd = map_name
	if game_mode != "":
		cmd += "?game=" + game_mode
	if len(mutators) > 0:
		cmd += "?mutator="
		cmd += ",".join(mutators)
	cmd += "?difficulty=" + str(difficulty)
	cmd += "?gamelength=" + str(game_length)
	if other_opt != "":
		cmd += other_opt

	cmd += " -useunpublished"
	cmd += " -languageforcooking=" + language_for_cooking
	cmd += " -log"
	return cmd

def launch_game(logger):
	launch_cmd = setup_launch_cmd()
	logger.info("Launching... " + launch_cmd)
	subprocess.run(kfeditor_dir + "\\KFGame.exe " + launch_cmd)

def commit():
	res = input("Leave messages: ")
	gitprocess("commit -m \"" + res + "\"")
	gitprocess("status")

def compile_mod(logger):
	try:
		# init
		setup_editor_cfg()

		# compile with tracking
		event_handler = MyHandler()
		observer = Observer()
		observer.schedule(event_handler, log_dir, recursive=False)
		observer.start()
		kfeditor = subprocess.Popen(kfeditor_dir + "\\kfeditor make")
		try:
			i = 0
			logger.info("Compiling...")
			while event_handler.log_mod_count < 2:
				time.sleep(1)

		finally:
			observer.stop()
			observer.join()
			kfeditor.terminate()

		# Automatically git add for successful compiling
		log_info = get_log_info()
		output_log("\n" + log_info["log"], logger)
		match log_info["state"]:
			case 0:
				gitprocess("add -A")
				gitprocess("status")
			case 2:
				sys.exit()

		# Game launch option
		launch_opt_msg = "Do you launch the game? [y/n]: "
		res = input(launch_opt_msg)
		while res.lower() != "y":
			if res.lower() == "n":
				sys.exit()
			logger.error("[ERROR] Wrong Input!!!")
			res = input(launch_opt_msg)

		launch_game(logger)

		commit_opt_msg = "Do you commit staged files? [y/n]: "
		res = input(commit_opt_msg)
		while res.lower() != "y":
			if res.lower() == "n":
				sys.exit()
			logger.error("[ERROR] Wrong Input!!!")
			res = input(commit_opt_msg)
		
		commit()

	except:
		sys.exit()

if __name__ == "__main__":
	try:
		logger = setup_logger()
		gitprocess("--version")
		gitprocess("status")
		res = input("0-Compile, 1-Test, 2-commit: ")
		if res == "0":
			compile_mod(logger)
		elif res == "1":
			launch_game(logger)
		elif res == "2":
			commit()
		else:
			logger.error("Aborted due to error")
			sys.exit()

	except:
		sys.exit()