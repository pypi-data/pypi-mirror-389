import json
import traceback
import bs4
from pathlib import Path
from bs4 import BeautifulSoup
import socket
from datetime import datetime
import webbrowser
from ClearData import SQLServerStoredProcedures

class ClearLogs:
	__SQLServerStoredProcedures__:SQLServerStoredProcedures

	__LogsFilePrefix__:str = None
	__LogsDirectory__:Path = None
	__LogJSONFilePath__:Path = None
	__LogHTMLFilePath__:Path = None
	__LogTextFilePath__:Path = None

	LogName:str
	InstanceNumber:int
	HostName:str
	IsInteractive:bool

	def __init__(self, connectionString:str, logName:str, logsPath:Path = None, logsFilePrefix:str = None, openInstance:bool = True, hostName:str = None, isInteractive:bool=False, commandLineArguments:list[str]|None=None):
		self.__SQLServerStoredProcedures__ = SQLServerStoredProcedures(connectionString)
		self.LogName = logName
		self.HostName = hostName if hostName is not None else socket.gethostname().lower()
		self.IsInteractive = isInteractive
		self.__LogsFilePrefix__ = logsFilePrefix
		if (logsPath is not None):
			self.__LogsDirectory__ = logsPath
			if (not self.__LogsDirectory__.exists()):
				self.__LogsDirectory__.mkdir(parents=True, exist_ok=True)
		if (not self.LogExists()):
			self.CreateLog()
		if (openInstance):
			self.OpenInstance()
			if (commandLineArguments is not None):
				if (len(commandLineArguments) > 1):
					arguments:dict[str, str] = dict[str, str]()
					for index, argument in enumerate(commandLineArguments):
						if (index > 0):
							if (":" in argument):
								argumentElements:list[str] = argument.split(":")
								if (len(argumentElements) == 2):
									arguments.update({argumentElements[0]: argumentElements[1]})
					if (len(arguments) > 0):
						self.WriteInstanceVariables(arguments, keyPrefix=f"CommandLineArguments.")

	def GetLogName(self, logId:int) -> str:
		returnValue:str = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetLogNameJSON",
					inputValue=json.dumps({"LogId": logId}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("LogName" in resultObj.keys()):
				returnValue = resultObj["LogName"]
		return returnValue

	def LogExists(self) -> bool:
		returnValue:bool = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetLogExistsJSON",
					inputValue=json.dumps({"LogName": self.LogName}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("LogExists" in resultObj.keys()):
				returnValue = resultObj["LogExists"]
		return returnValue

	def CreateLog(self):
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="CreateLogJSON",
					inputValue=json.dumps({"LogName": self.LogName}))

	def RemoveLog(self):
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="RemoveLogJSON",
					inputValue=json.dumps({"LogName": self.LogName}))

	def OpenInstance(self):
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON( "Logs", "OpenInstanceJSON",
					inputValue=json.dumps({ "LogName": self.LogName, "HostName": self.HostName }))
		if (result):
			resultObj:dict = json.loads(result)
			if ("InstanceNumber" in resultObj.keys()):
				self.InstanceNumber = resultObj["InstanceNumber"]
				if (self.__LogsDirectory__ is not None):
					filePath:Path = self.__LogsDirectory__.joinpath(f"{self.__LogsFilePrefix__}_{self.InstanceNumber:05d}").with_suffix(".ext")
					self.__LogJSONFilePath__ = Path(filePath).with_suffix(".json")
					self.__LogHTMLFilePath__ = Path(filePath).with_suffix(".html")
					self.__LogTextFilePath__ = Path(filePath).with_suffix(".txt")
					self.WriteInstanceFile(self.__LogJSONFilePath__, "Log File in JSON Format", "Log", self.HostName)
					self.WriteInstanceFile(self.__LogHTMLFilePath__, "Log File in HTML Format", "Log", self.HostName)
					self.WriteInstanceFile(self.__LogTextFilePath__, "Log File in Text Format", "Log", self.HostName)

	def CloseInstance(self, clearOldInstances:bool = True):
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly( "Logs", "CloseInstanceJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (clearOldInstances):
			self.ClearOldInstances()
		if (self.__LogsDirectory__ is not None):
			self.SaveInstance()
			self.SaveInstanceHTML()
			self.SaveInstanceText()
		if (self.IsInteractive):
			try:
				webbrowser.open_new_tab(self.__LogHTMLFilePath__)
			except:
				pass

	def WriteInstanceFile(self, path:Path, description:str = None, fileUse:dict = None, hostName:str = None):
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="WriteInstanceFileJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"HostName": hostName if hostName is not None else self.HostName,
						"FileUse": fileUse if fileUse is not None else "Log",
						"Path": str(path),
						"Description": description
					}))

	def SaveInstanceFile(self, fileName:str, description:str = None, fileUse:str = None, hostName:str = None, content:str = None) -> Path:
		returnValue:Path = self.__LogsDirectory__.joinpath(f"{self.__LogsFilePrefix__}_{self.InstanceNumber:05d}_{fileName}")
		returnValue.write_text(content if content is not None else "")
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="WriteInstanceFileJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"HostName": hostName if hostName is not None else self.HostName,
						"FileUse": fileUse if fileUse is not None else "Log",
						"Path": str(returnValue),
						"Description": description
					}))
		return returnValue

	def GetInstanceFiles(self, baseLogsURL:str|None = None, rootLogsPath:Path|None = None) -> list:
		returnValue:list = None
		includeURL:bool = (
			baseLogsURL is not None
			and rootLogsPath is not None)
		result:str = None
		if (includeURL):
			result = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceFilesJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"IncludeURL": True,
						"BaseLogsURL": baseLogsURL,
						"RootLogsPath": str(rootLogsPath)
					}))
		else:
			result = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceFilesJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"IncludeURL": False
					}))
		if (result):
			returnValue = json.loads(result)
		return returnValue

	def GetInstanceFilesText(self, baseLogsURL:str|None = None, rootLogsPath:Path|None = None) -> str:
		returnValue:str = None
		files:list = self.GetInstanceFiles(baseLogsURL, rootLogsPath)
		if (files is not None and len(files) > 0):
			if (baseLogsURL is not None
			and rootLogsPath is not None):
				for file in files:
					if (returnValue is None):
						returnValue = file["Description"] + ": " + file["URL"]
					else:
						returnValue += "\n" + file["Description"] + ": " + file["URL"]
			else:
				for file in files:
					if (returnValue is None):
						returnValue = file["Description"] + ": " + file["HostName"] + " " + file["Path"]
					else:
						returnValue += "\n" + file["Description"] + ": " + file["HostName"] + " " + file["Path"]
		return returnValue

	def WriteInstanceVariables(self, variables:dict, keyPrefix:str = None):
		variablesTransposed:list = []
		if (keyPrefix is None):
			keyPrefix = ""
		for key in variables:
			variablesTransposed.append({
				"Name": f"{keyPrefix}{key}",
				"Value": str(variables[key])
			})
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="WriteInstanceVariablesJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Variables": variablesTransposed
					}))

	def RemoveInstance(self):
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="RemoveInstanceJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (result):
			filesToDelete:dict = json.loads(result)
			if (filesToDelete):
				for file in filesToDelete:
					if (file["HostName"] == self.HostName and file["FileUse"] == "Log"):
						Path(file["Path"]).unlink(True)

	def ClearOldInstances(self):
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="ClearOldInstancesJSON",
					inputValue=json.dumps({ "LogName": self.LogName }))
		if (result):
			filesToDelete:dict = json.loads(result)
			if (filesToDelete):
				for file in filesToDelete:
					if (file["HostName"] == self.HostName and file["FileUse"] == "Log"):
						Path(file["Path"]).unlink(True)

	def GetLastInstanceNumber(self) -> int:
		returnValue:int = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetLastInstanceNumberJSON",
					inputValue=json.dumps({ "LogName": self.LogName }))
		if (result):
			resultObj:dict = json.loads(result)
			if ("InstanceNumber" in resultObj.keys()):
				returnValue = resultObj["InstanceNumber"]
		return returnValue

	def GetInstanceExceptionCount(self) -> int:
		returnValue:int = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceExceptionCountJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("ExceptionCount" in resultObj.keys()):
				returnValue = resultObj["ExceptionCount"]
		return returnValue

	def GetInstance(self) -> dict:
		returnValue:dict = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (result):
			returnValue = json.loads(result)
		return returnValue

	def SaveInstance(self):
		result = self.GetInstance()
		if (result is not None):
			if (self.__LogJSONFilePath__ is not None):
				with open(self.__LogJSONFilePath__, "w", encoding='utf-8') as file:
					file.write(json.dumps(result, indent="\t"))

	def GetInstanceHTML(self) -> str:
		returnValue:str = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceHTMLJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("HTML" in resultObj.keys()):
				returnValue = resultObj["HTML"]
		if (returnValue is not None):
			soup = BeautifulSoup(returnValue, "html.parser")
			returnValue = soup.prettify(formatter=bs4.formatter.HTMLFormatter(indent="\t"))
		return returnValue

	def SaveInstanceHTML(self):
		result:str = self.GetInstanceHTML()
		if (result is not None):
			if (self.__LogHTMLFilePath__ is not None):
				with open(self.__LogHTMLFilePath__, "w", encoding='utf-8') as file:
					file.write(result)

	def GetInstanceText(self, includeLineNumbers:bool = False) -> str:
		returnValue:str = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetInstanceTextJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"IncludeLineNumbers": includeLineNumbers
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("Text" in resultObj.keys()):
				returnValue = resultObj["Text"]
		return returnValue

	def SaveInstanceText(self, includeLineNumbers:bool = False):
		result:str = self.GetInstanceText(includeLineNumbers)
		if (result is not None):
			if (self.__LogTextFilePath__ is not None):
				with open(self.__LogTextFilePath__, "w", encoding='utf-8') as file:
					file.write(result)

	def GetLastSequence(self) -> int:
		returnValue:int = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="GetLastSequenceJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("Sequence" in resultObj.keys()):
				returnValue = resultObj["Sequence"]
		return returnValue

	def WriteEntry(self, text:str, rowCount:int = None, parentSequence:int = None,
				openTime:datetime = None, closeTime:datetime = None, sequence:int = None) -> int:
		returnValue:int = None
		openTimeString:str = None
		closeTimeString:str = None
		if (openTime is not None):
			openTimeString = openTime.isoformat()
		if (closeTime is not None):
			closeTimeString = closeTime.isoformat()
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="WriteEntryJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Text": text,
						"RowCount": rowCount,
						"ParentSequence": parentSequence,
						"OpenTime": openTimeString,
						"CloseTime": closeTimeString,
						"Sequence": sequence
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("Sequence" in resultObj.keys()):
				returnValue = resultObj["Sequence"]
		return returnValue

	def OpenEntry(self, text:str, rowCount:int = None, parentSequence:int = None) -> int:
		returnValue:int = None
		result:str = self.__SQLServerStoredProcedures__.ExecuteJSON(
					schema="Logs", name="OpenEntryJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Text": text,
						"RowCount": rowCount,
						"ParentSequence": parentSequence,
					}))
		if (result):
			resultObj:dict = json.loads(result)
			if ("Sequence" in resultObj.keys()):
				returnValue = resultObj["Sequence"]
		return returnValue

	def CloseEntry(self, sequence:int, text:str = None, rowCount:int = None):
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="CloseEntryJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Sequence": sequence,
						"Text": text,
						"RowCount": rowCount
					}))

	def WriteEntryVariables(self, sequence:int, variables:dict, keyPrefix:str = None):
		variablesTransposed:list = []
		if (keyPrefix is None):
			keyPrefix = ""
		for key in variables:
			variablesTransposed.append({
				"Name": f"{keyPrefix}{key}",
				"Value": str(variables[key])
			})
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="WriteEntryVariablesJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Sequence": sequence,
						"Variables": variablesTransposed
					}))

	def WriteException(self, sequence:int, exceptionInfo:tuple = None, data:dict = None, timestamp:datetime = None):
		timestampString:str = None
		if (timestamp is not None):
			timestampString = timestamp.isoformat()
		if (data is None and exceptionInfo is not None):
			data:dict = {
				"Type": exceptionInfo[0].__name__,
				"Value": str(exceptionInfo[1]),
				"Traceback": "".join(traceback.format_exception(*exceptionInfo)).strip()
			}
			for index, item in enumerate(exceptionInfo):
				if (index > 2):
					data.update({f"Element_{index}": str(item)})
		self.__SQLServerStoredProcedures__.ExecuteJSONInputOnly(
					schema="Logs", name="WriteExceptionJSON",
					inputValue=json.dumps({
						"LogName": self.LogName,
						"InstanceNumber": self.InstanceNumber,
						"Sequence": sequence,
						"Type": "PythonException",
						"Timestamp": timestampString,
						"Data": data
					}))

__all__ = ["ClearLogs"]