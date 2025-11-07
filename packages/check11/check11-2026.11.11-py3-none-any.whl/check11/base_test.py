import re
import sys
from colorama import Fore
from colorama import Style
import io
import traceback
import contextlib
from math import isclose
import importlib.util
from unittest.mock import patch, Mock
import unittest

class TestItem:
	def __init__(self):
		self._msg = None
		self._trace = None
		self._result = None

	def passed(self, b: bool):
		self._result = b

	def set_msg(self, msg):
		self._msg = msg

	def set_trace(self, trace):
		self._trace = trace

	def get_msg(self):
		return self._msg

	def get_trace(self):
		return self._trace

	def is_passed(self):
		return self._result

class TestSingle:
	def __init__(self, description: str, fname: str):
		self.desc = description
		self.items = list()
		self.current_item = None
		self.function = fname

	def make_test_desc(self):
		return f"Tested: {Style.BRIGHT}{self.function}{Style.NORMAL}(). {self.get_desc()}"

	def get_desc(self):
		return self.desc

	def get_items(self):
		return self.items

	def has_items(self):
		return len(self.items) > 0

	def new_item(self) -> TestItem:
		self.current_item = TestItem()
		self.items.append(self.current_item)
		return self.current_item

	def current(self):
		return self.current_item

class BaseTest: # for a complete module with more functions and tests
	def __init__(self, experiment_path, experiment, verbose, trace):
		self.verbose = verbose
		self.trace = trace
		self.path_for_testing = experiment_path
		self.name_for_testing = experiment
		self.mod_for_testing = None
		self.functions_for_testing = list()
		self.test_mod = None
		self.test_functions = dict()
		self.tests = list()

		e_mod = self.name_for_testing.replace('.py', '')
		if not self.load_module_for_testing():
			print(f"Module {experiment} cannot be found or tested")
			sys.exit(1)

		self.set_methods_in_runtest(self)
		if not self.exist_functions():
			return
		self.run_all_tests()

	def __str__(self):
		return self.report_as_string()

	def load_module_for_testing(self) -> bool:
		try:
			specs = importlib.util.spec_from_file_location(self.name_for_testing, self.path_for_testing)
			# add to sys modules
			sys.modules[self.name_for_testing] = importlib.util.module_from_spec(specs)
			# load
			specs.loader.exec_module(sys.modules[self.name_for_testing])
			self.mod_for_testing = sys.modules[self.name_for_testing]
			return True
		except:
			self.mod_for_testing = None
			return False

	def set_methods_in_runtest(self, tm):
		self.test_functions = dict()
		self.test_mod = tm
		for f in dir(self.test_mod):
			if not f.startswith('test_'):
				continue
			func = getattr(self.test_mod, f)
			self.test_functions[f] = func

	def get_linux_path(self, s: str) -> str|None:
		# returns a list with paths if found in string
		pattern = '\"/(.*?)\"'
		res = re.findall(pattern, s, re.I|re.M)
		if len(res) == 0:
			return None
		return '/'+res[0]

	def traceback_on_exception(self) -> list:
		# moet de output beperken tot relevante regels
		myFile = io.StringIO()
		traceback.print_exc(file=myFile)
		# foutmelding
		lines = myFile.getvalue()
		lines = lines.split('\n')
		lines.reverse()
		relevant = True
		rlines = list()
		for i in range(len(lines)):
			if not relevant:
				continue

			lpath = self.get_linux_path(lines[i])
			if lpath is None:
				# houd line in lijst
				rlines.append(lines[i])
				continue

			# na eerste linux-path, relevance stopt
			if not 'utest.py' in lpath and not 'base_test.py' in lpath and not 'assert' in lpath and not 'AssertionError' in lpath:
				# laatste relevante regel
				shortpath = lpath.split('/')[-1]
				line = lines[i].replace(lpath, f"/{shortpath}").strip()
				line = line.replace("\t", "").replace("  ", " ").replace("\n", "")
				if line.isspace():
					continue
				rlines.append(line)
				relevant = False
		rlines.reverse()
		return rlines

	def caught_exception(self) -> str:
		e = traceback.format_exc()
		lines = e.splitlines()
		# laatste regel bevat exceptions
		return lines[-1].strip().split(":")[0]

	def set_argv(self, args: list):
		sys.argv = ['']
		sys.argv.extend(args)

	def comargs_params_text(self, comargs: list, params: list, promptin: str|None) -> str:
		# returns info for output
		withwhat = ""
		withand = "with"
		if len(comargs) > 0:
			withwhat = f"with command line arguments {Style.BRIGHT}{comargs}{Style.NORMAL}"
			withand = " and"
		if len(params) > 0:
			withwhat = f"{withwhat}{withand} parameters {Style.BRIGHT}{params}{Style.NORMAL}"
			withand = " and"
		if not promptin is None:
			withwhat = f"{withwhat}{withand} prompt input {Style.BRIGHT}{promptin}{Style.NORMAL}"
			withand = " and"
		return withwhat

	def get_score_percent(self) -> float:
		total = 0
		passed = 0
		for test in self.tests:
			for testitem in test.get_items():
				total += 1
				if testitem.is_passed():
					passed += 1
		return round(float(passed / total)*100, 1)

	def make_traceback_message(self, funcname: str, pars: str, msg: str):
		m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} -- {msg}, see traceback"
		if self.trace:
			m += ' below for details'
		else:
			m += ' for details'
		return m

	def get_report(self) -> list:
		def all_passed(test):
			ap = True
			for testitem in test.get_items():
				ap = ap and testitem.is_passed()
			return ap

		u_on = "\033[4m"
		u_off = "\033[0m"
		newline = ""
		lines = list()
		count_passed = 0
		count_failed = 0

		line = f"{Style.BRIGHT}{Fore.BLUE}••••••••••••••• testing {self.name_for_testing}.py •••••••••••••••{Style.RESET_ALL}"
		lines.append(line)
		for test in self.tests:
			ap = all_passed(test)
			if not test.has_items():
				continue

			if not ap:
				if self.verbose and test.get_desc() != "":
					lines.append(test.make_test_desc())

			for testitem in test.get_items():
				if testitem.get_msg() is None:
					continue
				if testitem.get_msg() == '':
					continue

				if testitem.is_passed():
					count_passed += 1
					lines.append(f"\t{Fore.GREEN}PASSED::{Style.RESET_ALL} {testitem.get_msg()}")
				else:
					count_failed += 1
					lines.append(f"\t{Fore.RED}FAILED:: {testitem.get_msg()}{Style.RESET_ALL}")

				# traceback from here
				if not self.trace or testitem.get_trace() is None:
					continue
				if len(testitem.get_trace()) == 0:
					continue

				lines.append(newline)
				lines.append(f"\t------------ traceback ------------")
				for line in testitem.get_trace():
					lines.append(f"\t{line}")
				lines.append(f"\t------------ end traceback --------")
				lines.append(newline)
			# end per testitem
		# end per test

		percent = int(round(self.get_score_percent(), 0))
		lines.append(f"{Fore.BLUE}••••••••••••••• finished {Fore.GREEN}tests passed: {count_passed}{Fore.RED} tests failed: {count_failed}{Fore.BLUE} score: {percent}% •••••••••••••••{Style.RESET_ALL}")
		return lines

	def report_as_string(self):
		r = self.get_report()
		lines = ""
		for line in r:
			lines = f"{lines}\n{line}"
		return lines

	def run_all_tests(self):
		for funcname in self.test_functions:
			try:
				func = getattr(self.test_mod, funcname)
				func()
			except:

				pass

	# ================= actual tests =================
	# SINGLE test if value in, value out of function match, with single parameter
	def exist_functions(self) -> bool:
		# if not ok, other tests do not run
		fnames = self.mandatory_functions()
		testname_plus = f"functions exist: {fnames}"
		test = TestSingle(testname_plus, "")
		self.tests.append(test)
		current_test = test.new_item()
		not_exist = list()
		for fname in fnames:
			try:
				func = getattr(self.mod_for_testing, fname)
				self.functions_for_testing.append(func)
			except:
				not_exist.append(fname)
		if len(not_exist) == 0:
			current_test.passed(True)
			current_test.set_msg(f"all functions exist: {Style.BRIGHT}{fnames}{Style.NORMAL}")
		else:
			current_test.passed(False)
			current_test.set_msg(f"functions {Style.BRIGHT}{not_exist}{Style.NORMAL} missing")

		return len(not_exist) == 0

	# COMPLEX single test with parameters, command line args
	def assert_params_comargs(self, funcname: str, testname: str, expected, parameters, comargs: list, howclose=0.0, testtype=False):
		modpy = f"{self.name_for_testing}.py"
		test = TestSingle(testname, funcname)
		current_test = test.new_item()
		pars = str(parameters)
		self.tests.append(test)

		self.set_argv(comargs)
		try:
			func = getattr(self.mod_for_testing, funcname)
			r = func(*parameters)
		except:
			current_test.passed(False)
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'some other error occurred'))
			current_test.set_trace(self.traceback_on_exception())
			return

		withwhat = self.comargs_params_text(comargs, parameters, None)

		try:
			if howclose > 0.0 :
				assert isclose(r, expected, rel_tol=howclose, abs_tol=0.0)
			elif testtype:
				assert type(r) == expected
			else:
				assert r == expected
		except AssertionError:
			m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} EXPECTED output {Style.BRIGHT}{expected}{Style.NORMAL}, but RECEIVED {Style.BRIGHT}{r}{Style.NORMAL}"
			current_test.passed(False)
			current_test.set_msg(m)
			# current_test.set_trace(self.traceback_on_exception())
			return
		except:
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'some other error occurred'))
			current_test.passed(False)
			current_test.set_trace(self.traceback_on_exception())
			return

		# test passed
		m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} RECEIVED {Style.BRIGHT}{r}{Style.NORMAL}"

		# test passed
		current_test.passed(True)
		current_test.set_msg(m)
		return

	# test for raised errors in code
	def raise_error(self, funcname: str, testname, expected, parameters, comargs):
		modpy = f"{self.name_for_testing}.py"
		pars = str(parameters)
		test = TestSingle(testname, funcname)
		current_test = test.new_item()
		self.tests.append(test)

		self.set_argv(comargs)
		func = getattr(self.mod_for_testing, funcname)
		try:
			r = func(*parameters)
			caught_exception = r
		except:
			caught_exception = str(self.caught_exception())

		withwhat = self.comargs_params_text(comargs, parameters, None)
		# test received error
		try:
			assert expected == caught_exception
			# passed test
		except AssertionError:
			# failed test
			m = f"raise error {Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} EXPECTED {Style.BRIGHT}{expected}{Style.NORMAL}, but RECEIVED {Style.BRIGHT}{caught_exception}{Style.NORMAL}"
			current_test.passed(False)
			current_test.set_msg(m)
			return
		except:
			current_test.passed(False)
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'some other error occurred'))
			current_test.set_trace(self.traceback_on_exception())
			return

		# passed
		m = f"raise error {Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} RECEIVED {Style.BRIGHT}{caught_exception}{Style.NORMAL}"
		current_test.passed(True)
		current_test.set_msg(m)
		return

	# test for proper exit message or value
	def sys_exit(self, funcname: str, testname: str, expected, parameters, comargs):
		# test if program has sys.exit with proper exit value
		pars = str(parameters)
		modpy = f"{self.name_for_testing}.py"
		withwhat = self.comargs_params_text(comargs, parameters, None)
		test = TestSingle(testname, funcname)
		current_test = test.new_item()
		self.tests.append(test)
		try:
			func = getattr(self.mod_for_testing, funcname)
			ut = unittest.TestCase()
			with ut.assertRaises(SystemExit) as cm:
				func(*parameters)
			r = cm.exception.code
			assert r == expected
		except AssertionError:
			m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} EXPECTED exit message {Style.BRIGHT}{expected}{Style.NORMAL}, but RECEIVED exit message {Style.BRIGHT}{r}{Style.NORMAL}"
			current_test.passed(False)
			current_test.set_msg(m)
			return
		except:
			current_test.passed(False)
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'an unknown other error occurred'))
			current_test.set_trace(self.traceback_on_exception())
			return

		m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} has EXIT MESSAGE {Style.BRIGHT}{r}{Style.NORMAL}"
		current_test.passed(True)
		current_test.set_msg(m)
		return

	# test with possible prompt input output
	def input_and_or_output(self, funcname: str, testname, expected, parameters, comargs, erin: str|None=None, eruit: str|None=None):
		modpy = f"{self.name_for_testing}.py"
		pars = str(parameters)
		test = TestSingle(testname, funcname)
		current_test = test.new_item()
		self.tests.append(test)
		self.set_argv(comargs)
		# erin PROMPT or not
		try:
			func = getattr(self.mod_for_testing, funcname)
			if erin is None:
				if not eruit is None:
					f = io.StringIO()
					with contextlib.redirect_stdout(f):
						func(*parameters)
					r = f.getvalue()
					expected = eruit
					hoeuit = f"prompt output"
				else:
					r = func(*parameters)
					hoeuit = f"output"
			else:
				with patch('builtins.input', lambda _: erin):
					if not eruit is None:
						f = io.StringIO()
						with contextlib.redirect_stdout(f):
							func(*parameters)
						r = f.getvalue()
						expected = eruit
						hoeuit = f"prompt output"
					else:
						r = func(*parameters)
						hoeuit = f"output"
		except:
			current_test.passed(False)
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'an error occurred'))
			current_test.set_trace(self.traceback_on_exception())
			return

		withwhat = self.comargs_params_text(comargs, parameters, erin)
		#  now test it with expected exit msg
		try:
			r = str(r)
			r = r.replace("\n", "")
			expected = str(expected)
			assert r.strip() == expected.strip()
		except AssertionError:
			m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} EXPECTED {hoeuit} {Style.BRIGHT}{expected}{Style.NORMAL}, but RECEIVED exit message {Style.BRIGHT}{r}{Style.NORMAL}"
			current_test.passed(False)
			current_test.set_msg(m)
			return
		except:
			current_test.passed(False)
			current_test.set_msg(self.make_traceback_message(funcname, pars, 'some other error occurred'))
			current_test.set_trace(self.traceback_on_exception())
			return

		m = f"{Style.BRIGHT}{funcname}{pars}{Style.NORMAL} {withwhat} has {hoeuit} {Style.BRIGHT}{expected}{Style.NORMAL}"
		current_test.passed(True)
		current_test.set_msg(m)
		return


