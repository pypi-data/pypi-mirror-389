import pickle
from datetime import datetime
import pytz
import time
import urllib.request
import certifi
import ssl
import requests
from colorama import Style, Fore, Back
import os
from inspect import currentframe, getframeinfo
import platformdirs

class Ins:
	@classmethod
	def info(cls):
		return f"[{cls.script()}|{cls.func()}|{cls.line()}]"

	@classmethod
	def script(cls):
		try:
			return getframeinfo(currentframe()).filename
		except:
			return '-'

	@classmethod
	def func(cls):
		try:
			return currentframe().f_code.co_name
		except:
			return '-'

	@classmethod
	def line(cls):
		try:
			return getframeinfo(currentframe()).lineno
		except:
			return '-'

class ErrorLogMeta(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			instance = super().__call__(*args, **kwargs)
			cls._instances[cls] = instance
		return cls._instances[cls]

class ErrorLog(metaclass=ErrorLogMeta):
	force = False

	def __init__(self):
		self.path = os.path.join(os.getcwd(), 'check11.log')
		self.add('start log', Timetools.now_string(), first=True)

	def __del__(self):
		try:
			self.close_log()
		except:
			pass

	def set_force(self, force):
		self.force = force

	def close_log(self):
		self.add('end log', Timetools.now_string())

	def set_path(self, path):
		self.path = path

	def add(self, where: str, msg: str, first=False):
		# self.msgs.append([where, msg])
		if first:
			mode = 'w'
		else:
			mode = 'a'
		if self.force:
			with open(self.path, mode=mode) as handle:
				handle.write(f"{where}\t{msg}\n")

class Css:
	# uses colorama for creating style in prompt
	@classmethod
	def reset(cls) -> str:
		return f"{Style.RESET_ALL}"

	@classmethod
	def normal(cls, s=None) -> str:
		if s is None:
			return f"{Style.NORMAL}"
		return f"{cls.normal()}{s}{cls.reset()}"

	@classmethod
	def href(cls, uri, label=None):
		if label is None:
			label = uri
		parameters = ''
		# OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
		escape_mask = '\033]8;{};{}\033\\{}\033]8;;\033\\'
		return escape_mask.format(parameters, uri, label)

	@classmethod
	def jippie(cls, s=None) -> str:
		if s is None:
			return f"{Fore.BLUE}{Style.BRIGHT}"
		else:
			return f"{cls.jippie()}{s}{cls.reset()}"

	@classmethod
	def bold(cls, s=None) -> str:
		if s is None:
			return f"{Style.BRIGHT}"
		return f"{cls.bold()}{s}{cls.reset()}"

	@classmethod
	def good(cls, s=None) -> str:
		if s is None:
			return f"{Fore.LIGHTGREEN_EX}{Style.BRIGHT}"
		return f"{cls.good()}{s}{cls.reset()}"

	@classmethod
	def warning(cls, s=None) -> str:
		if s is None:
			return f"{Fore.LIGHTCYAN_EX}{Style.BRIGHT}"
		return f"{cls.warning()}{s}{cls.reset()}"

	@classmethod
	def attention(cls, s=None) -> str:
		# more serious than warn
		if s is None:
			return f"{Back.LIGHTYELLOW_EX}{Fore.BLACK}{Style.BRIGHT}"
		return f"{cls.attention()} {s} {cls.reset()}"

	@classmethod
	def wrong(cls, s=None) -> str:
		if s is None:
			return f"{Fore.LIGHTRED_EX}{Style.BRIGHT}"
		return f"{cls.wrong()}{s}{cls.reset()}"

	@classmethod
	def prompt(cls, s=None) -> str:
		if s is None:
			return f"{Fore.BLACK}{Style.BRIGHT}"
		return f"{cls.prompt()}{s}{cls.reset()}"

	@classmethod
	def log(cls) -> str:
		return f"{Fore.MAGENTA}{Style.NORMAL}"

# General function for type casting
class Casting:
	@classmethod
	def str_(cls, erin, default: str | None='') -> str | None:
		try:
			return str(erin)
		except:
			return default

	@classmethod
	def int_(cls, erin, default: int | None=0) -> int | None:
		try:
			return int(erin)
		except:
			return default

	@classmethod
	def float_(cls, erin, default=0.0) -> float:
		try:
			return float(erin)
		except:
			return default

	@classmethod
	def bool_(cls, erin, default=True) -> bool:
		try:
			return bool(erin)
		except:
			return default

	@classmethod
	def listint_(cls, erin, default=[]):
		try:
			for i in range(len(erin)):
				erin[i] = int(erin[i])
			return erin
		except:
			return default

	@classmethod
	def liststr_(cls, erin, default=[]):
		try:
			for i in range(len(erin)):
				erin[i] = str(erin[i])
			return erin
		except:
			return default

	@classmethod
	def cast(cls, erin, intotype, default=None) -> any:
		if intotype == int:
			if default is None:
				return cls.int_(erin)
			else:
				return cls.int_(erin, default=default)
		elif intotype == float:
			if default is None:
				return cls.float_(erin)
			else:
				return cls.float_(erin, default=default)
		elif intotype == bool:
			if default is None:
				return cls.bool_(erin)
			else:
				return cls.bool_(erin, default=default)
		return str(erin).strip()

	@classmethod
	def typecast_list(cls, l: list, t: type) -> list:
		try:
			return list(map(t, l))
		except Exception as e:
			return []

# General functions for working with time
class Timetools:
	TTIMESTRING = "%Y%m%dT%H00"
	DATETIME_LOCAL = "%Y-%m-%dT%H:%M"
	DATETIMESTRING = "%Y-%m-%d %H:%M:%S"
	DATETIMESTRING_NL = "%d-%m-%Y %H:%M:%S"
	DATESTRING = "%Y-%m-%d"
	DATESTRING_NL = "%d-%m-%Y"
	BIRTH = '1972-02-29'

	@classmethod
	def dtlocal_2_ts(cls, tts: str):
		try:
			dt = datetime(
				year=int(tts[0:4]),
				month=int(tts[5:7]),
				day=int(tts[8:10]),
				hour=int(tts[11:13]),
				minute=int(tts[14:16])
			)
			return int(dt.timestamp())
		except:
			return Timetools.td_2_ts(cls.BIRTH)

	@classmethod
	def dtonixzips_2_tms(cls, tts: str):
		try:
			dt = datetime(
				year=int(tts[0:4]),
				month=int(tts[5:7]),
				day=int(tts[8:10]),
				hour=int(tts[11:13]),
				minute=int(tts[14:16]),
				second=int(tts[17:19]),
				microsecond=int(tts[20:])
			)
			return int(dt.timestamp() * 1000)
		except Exception as e:
			return Timetools.td_2_ts(cls.BIRTH) * 1000

	@classmethod
	def td_2_ts(cls, datum: str) -> int:
		# convert date-string yyyy-mm-dd to seconds timestamp
		try:
			dt = datetime(
				year=int(datum[0:4]),
				month=int(datum[5:7]),
				day=int(datum[8:10]),
			)
			return int(dt.timestamp())
		except:
			return Timetools.td_2_ts(cls.BIRTH)

	@classmethod
	def tdtime_2_ts(cls, datumtijd: str) -> int:
		# convert date-string yyyy-mm-dd to seconds timestamp
		try:
			dt = datetime(
				year=int(datumtijd[0:4]),
				month=int(datumtijd[5:7]),
				day=int(datumtijd[8:10]),
				hour=int(datumtijd[11:13]),
				minute=int(datumtijd[14:16]),
				second=int(datumtijd[17:19]),
			)
			return int(dt.timestamp())
		except:
			return Timetools.td_2_ts(cls.BIRTH)

	@classmethod
	def ts_2_td(cls, timest: int, rev=False, withtime=False) -> str:
		# convert seconds to datestring yyyy-mm-dd
		if withtime:
			if rev:
				dstr = cls.DATETIMESTRING
			else:
				dstr = cls.DATETIMESTRING_NL
		else:
			if rev:
				dstr = cls.DATESTRING
			else:
				dstr = cls.DATESTRING_NL
		try:
			return datetime.fromtimestamp(timest, pytz.timezone("Europe/Amsterdam")).strftime(dstr)
		except:
			return ''

	@classmethod
	def now(cls) -> float:
		return time.time()

	@classmethod
	def now_secs(cls) -> int:
		# for normal use
		return int(cls.now())

	@classmethod
	def now_milisecs(cls) -> int:
		# for use in generating unique numbers
		return int(cls.now() * 1000)

	@classmethod
	def now_nanosecs(cls) -> int:
		# not preferred
		return int(cls.now() * 1000000)

	@classmethod
	def ts_2_datetimestring(cls, ts: int|float|None, rev=False, noseconds=False):
		if rev:
			dstr = cls.DATETIMESTRING
		else:
			dstr = cls.DATETIMESTRING_NL
		if noseconds:
			dstr = dstr[:-3]
		if ts is None:
			ts = cls.now()
		if isinstance(ts, int):
			if len(str(ts)) > 11:
				ts = ts / 1000 # nanoseconds
		if not isinstance(ts, float):
			ts = Casting.float_(ts, 0) # adding trailing zero's representing ms and ns
		return datetime.fromtimestamp(ts, pytz.timezone("Europe/Amsterdam")).strftime(dstr)

	@classmethod
	def ts_2_datestring(cls, ts: int | float | None, rev=False):
		if rev:
			dstr = cls.DATESTRING
		else:
			dstr = cls.DATESTRING_NL

		if ts is None:
			ts = cls.now()
		if isinstance(ts, int):
			if len(str(ts)) > 13:
				ts = ts / 1000000  # nanoseconds
			elif len(str(ts)) > 11:
				ts = ts / 1000  # milliseconds
		if not isinstance(ts, float):
			ts = Casting.float_(ts, 0)  # adding trailing zero's representing ms and ns
		return datetime.fromtimestamp(ts, pytz.timezone("Europe/Amsterdam")).strftime(dstr)

	@classmethod
	def now_string(cls) -> str:
		return datetime.fromtimestamp(cls.now(), pytz.timezone("Europe/Amsterdam")).strftime(cls.DATETIMESTRING)
		# return str(datetime.strptime(timestamp, cls.DATETIMESTRING))

	@classmethod
	def datetimenow(cls):
		return datetime.now()

	@classmethod
	def draaiom(cls, erin):
		# changes yyyy-mm-dd into dd-mm-yyyy and vv
		try:
			d = erin.split('-')
			return f'{d[2]}-{d[1]}-{d[0]}'
		except:
			return erin

class GithubJeex:
	@staticmethod
	def con_repo_list():
		pass

	@staticmethod
	def con_repo_path(token, assignment) -> dict|None:
		log = ErrorLog()
		# gets all the info about a repo
		data = data = {
			"Accept": "application/vnd.github+json",
			"Authorization": f"Bearer {token}",
			"X-GitHub-Api-Version": "2022-11-28",
		}
		url = f'https://api.github.com/repos/jeex/jeex_public/contents/{assignment}'
		try:
			response = requests.get(
				url,
				data
			)
		except Exception as e:
			log.add(Ins.info(), str(e))
			return None
		try:
			return response.json()
		except Exception as e:
			log.add(Ins.info(), str(e))
			return None

	@staticmethod
	def con_repo_download(url, fpath) -> bool:
		log = ErrorLog()
		try:
			with urllib.request.urlopen(url, context=ssl.create_default_context(cafile=certifi.where())) as handle:
				script = handle.read().decode()
			with open(fpath, 'w') as handle:
				handle.write(script)
			return True
		except Exception as e:
			log.add(Ins.info(), str(e))
			return False
		
class LocalUser:
	_expire = 1000 * 60 * 60 * 48 # twee dagen
	def __init__(self):
		# self._expire = 1000 * 60
		pass

	def expired(self, toens) -> bool:
		nus = Timetools.now_milisecs()
		return toens + self._expire < nus

	# keeps user data locally
	def get_path(self):
		path = platformdirs.user_data_dir("monze.eu")
		if not os.path.isdir(path):
			os.makedirs(path)
		return os.path.join(path, "check11_settings.pickle")

	def set(self, d: dict) -> bool:
		# sets user in local settings file
		nus = Timetools.now_milisecs()
		d['nus'] = nus
		try:
			with open(self.get_path(), "wb") as handle:
				pickle.dump(d, handle)
			return True
		except:
			pass
		return False

	def get(self) -> dict | None:
		# gets user from local settings file
		nus = Timetools.now_milisecs()
		try:
			with open(self.get_path(), "rb") as handle:
				d = pickle.load(handle)
			# check if expired
			if self.expired(d['nus']):
				self.remove()
				return None
			return d
		except:
			pass
		return None

	def remove(self):
		try:
			os.remove(self.get_path())
		except:
			pass

