import shutil
import sys
import os
import importlib.util
import pathlib
import requests

dbbpath = str(pathlib.Path(__file__).parent.resolve())
if not dbbpath in sys.path:
	sys.path.insert(0, dbbpath)

from prompt_helpers import (
	GithubJeex,
	Casting,
	Css,
	Timetools,
	ErrorLog,
	Ins,
	LocalUser,
)

class DbGlo:
	# globals for this app
	gloos = dict(
		_VERSION = '2026.11.001',
		_APP_NAME = 'check11',
		_DEV = False,
	)
	@classmethod
	def get(cls, s: str):
		return cls.gloos[s]

def check_version():
	githuburl = "https://raw.githubusercontent.com/jeex/jeex_public/refs/heads/main/check11_version.txt"
	try:
		r = requests.get(githuburl)
	except:
		sys.exit("Github not available")
	if r.status_code != 200:
		sys.exit("Github version.txt not available")
	dbb_version = r.content.decode("utf-8").strip()
	# print(dbb_version, DbGlo.get("_VERSION"))
	if dbb_version > DbGlo.get("_VERSION"):
		print(f"{Css.warning()}This version is {DbGlo.get('_VERSION')}. Upgrade with newer version {dbb_version} with: {Css.reset()}\n\tpip install check11 --upgrade --no-cache-dir")
		sys.exit(1)

def print_help():
	print(f"How to use check11 when your experiment is called {Css.bold()}my_exp.py{Css.reset()}: "
	      f"\n\t{Css.bold()}check11 -h{Css.reset()} for help"
	      f"\n\t{Css.bold()}check11 my_exp.py{Css.reset()} to run the test"
	      f"\n\t{Css.bold()}check11 my_exp.py -c{Css.reset()} to run the test, and clear terminal first"
	      f"\n\t{Css.bold()}check11 my_exp.py -v{Css.reset()} to run the test, with more info about errors"
	      f"\n\t{Css.bold()}deebecheck11ebros my_exp.py -t{Css.reset()} to run the test, with traceback for errors"
	      f"\n\t{Css.bold()}check11 my_exp.py -c -t -v{Css.reset()} to run the test, combining arguments"
      )

def from_args():
	email = experiment = None
	verbose = False
	clear = False
	trace = False
	phelp = False
	# results = False
	forcelog = False
	for arg in sys.argv[1:]:
		arg = arg.strip().lower()
		if arg in ['-v', '--verbose']:
			verbose = True
			continue
		if arg in ['-c', '--clear']:
			clear = True
			continue
		if arg in ['-t', '--trace']:
			trace = True
			continue
		if arg in ['-h', '--help']:
			phelp = True
			continue
		if arg in ['-l', '--forcelog']:
			forcelog = True
			continue
		if arg == '-version':
			print(DbGlo.get("_VERSION"))
			sys.exit(0)
		if arg.endswith('.py'):
			experiment = arg
			continue

	# show help
	if phelp:
		print_help()
		sys.exit(1)

	return experiment, verbose, trace, clear, forcelog

def download_unittest(check11pad, experiment):
	unittestname = get_unittest_name(experiment)
	print(f"Downloading unittest file for [{experiment}]...", end="")
	unittest_durl = f'https://raw.githubusercontent.com/jeex/jeex_public/refs/heads/main/check11_unittests/{unittestname}'
	if not GithubJeex().con_repo_download(unittest_durl, os.path.join(check11pad, unittestname)):
		print(f" failed")
		sys.exit(1)
	print(Css.good(" ready"))

def get_unittest_name(experiment):
	return f'check11_{experiment}'

def upload_test(experiment: str, check11pad: str):
	cwd = os.getcwd()
	source_path = os.path.join(cwd, experiment)
	target_path = os.path.join(check11pad, experiment)
	try:
		shutil.copy(source_path, target_path)
	except:
		print(Css.wrong(f"The file [{experiment}] does not exist in the directory [{cwd}]"))
		sys.exit(1)
	if not os.path.isfile(target_path):
		print(Css.wrong(f"The file [{experiment}] cannot be tested"))
		sys.exit(1)

def load_base_test_class(pad: str):
	try:
		# load basetest class
		specs = importlib.util.spec_from_file_location('base_test', os.path.join(pad, 'base_test.py'))
		# add to sys modules
		sys.modules['base_test'] = importlib.util.module_from_spec(specs)
		# load
		specs.loader.exec_module(sys.modules['base_test'])
	except Exception as e:
		print(Css.wrong("Base Test class is unavailable"))
		sys.exit(1)

def this_test_mod(modpath: str, modname: str):
	try:
		specs = importlib.util.spec_from_file_location(modname, modpath)
		sys.modules[modname] = importlib.util.module_from_spec(specs)
		specs.loader.exec_module(sys.modules[modname])
		return sys.modules[modname]
	except Exception as e:
		print(Css.wrong(f"The module [{modname}.py] cannot be loaded"))
		# print(e)
		sys.exit(1)

def clear_terminal():
	try:
		os.system('cls' if os.name == 'nt' else 'clear')
	except:
		pass

def testing_api_check(mon, report, percent, experiment):
	check = {
		'user': mon.gho.get_alias(),
		'experiment': experiment,
		'checked': Timetools.now_string(),
		'percent': percent,
		'report': report
	}
	print('update check result', mon.update_check(check))

def main():
	log = ErrorLog()
	check_version()
	check11_pad = os.path.join(os.path.dirname(__file__), 'unittests')
	if not os.path.isdir(check11_pad):
		try:
			os.makedirs(check11_pad)
		except Exception as e:
			log.add(Ins.info(), str(e))
			print(Css.wrong('No place for testing in your computer. Contact Monze.EU'))
			sys.exit(1)

	# read all stuff from command line args
	experiment, verbose, trace, clear, forcelog = from_args()
	log.set_force(forcelog)

	if clear:
		clear_terminal()

	# check experiment
	if experiment is None:
		print(f"{Css.wrong()}No valid experiment in command line args. Use: {Css.reset()}check11 -h{Css.wrong()} for help{Css.reset()}")
		print_help()
		sys.exit(1)
	cwd = os.getcwd()
	if not os.path.isfile(os.path.join(cwd, experiment)):
		print(Css.wrong(f"Invalid experiment name: [{experiment}] does not exist in path: {os.getcwd()}"))
		sys.exit(1)

	# download unittest, exits if wrong
	download_unittest(check11_pad, experiment)

	# upload the script experiment to unittests folder
	upload_test(experiment, check11_pad)

	# load test mod
	load_base_test_class(os.path.dirname(__file__))
	experiment_path = os.path.join(check11_pad, experiment)
	unittest_path = os.path.join(check11_pad, get_unittest_name(experiment))
	unittest_mod = this_test_mod(unittest_path, get_unittest_name(experiment))

	# start test class
	tm = unittest_mod.RunTest(
		experiment_path,
		experiment,
		verbose,
		trace,
	)
	# print results
	report = tm.get_report()
	percent = tm.get_score_percent()
	# print the report in the terminal
	print(tm)
	print()

if __name__ == "__main__":
	main()