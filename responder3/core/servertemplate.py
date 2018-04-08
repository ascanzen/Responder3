import abc
import hashlib
import asyncio
import logging
import datetime
import enum
import socket
import os
import io
import traceback
import copy

from responder3.core.commons import *

class ResponderServerSession(abc.ABC):
	def __init__(self, connection):
		self.connection = connection

class ResponderServer(abc.ABC):
	def __init__(self, connection, session, serverprops, globalsession = None, loop = None):
		self.loop = loop
		if self.loop is None:
			self.loop = asyncio.get_event_loop()
		self.session = session
		self.caddr   = (session.connection.remote_ip, 
						session.connection.remote_port)
		self.creader = connection[0]
		self.cwriter = connection[1]
		self.logQ    = serverprops.shared_logQ
		self.rdns    = serverprops.shared_rdns
		self.protocol= serverprops.bind_protocol
		self.sprops  = serverprops
		self.modulename = '%s-%s' % (self.sprops.serverhandler.__name__, self.protocol.name)
		self.settings= copy.deepcopy(serverprops.settings)
		self.globalsession = globalsession

		self.init()

	@abc.abstractmethod
	def init(self):
		pass

	def log(self, message, level = logging.INFO):
		"""
		Create a log message and send it to the LogProcessor for procsesing
		"""
		#if session is None or self.session.connection.remote_ip == None:
		#	message = '[INIT] %s' %  message
		#else:	
		#	message = '[%s:%d] %s' % (self.session.connection.remote_ip, self.session.connection.remote_port, message)
		message = '[%s:%d] <-> [%s:%d] %s' % (self.sprops.bind_addr, self.sprops.bind_port,
												self.session.connection.remote_ip, 
												self.session.connection.remote_port,
												message)
		self.logQ.put(LogEntry(level, self.modulename, message))

	def logCredential(self, credential):
		"""
		Create a Result message and send it to the LogProcessor for procsesing
		"""
		credential.module = self.modulename
		credential.client_addr = self.session.connection.remote_ip
		credential.client_rdns = self.session.connection.remote_ip
		self.logQ.put(credential)

	
	#def logConnection(self):
	#	"""
	#	Create a Connection message and send it to the LogProcessor for procsesing
	#	connection: A connection object that holds the connection info for the client
	#	"""
	#	if self.session.connection.status == ConnectionStatus.OPENED or self.session.connection.status == ConnectionStatus.STATELESS:
	#		self.log(logging.INFO, 'New connection opened', self.session)
	#	elif self.session.connection.status == ConnectionStatus.CLOSED:
	#		self.log(logging.INFO, 'Connection closed', self.session)
	#	self.logQ.put(self.session.connection)
	

	def logPoisonResult(self, requestName = None, poisonName = None, poisonIP = None):
		self.log('Resolv request in!')
		pr = PoisonResult()
		pr.module = self.modulename
		pr.target = self.session.connection.remote_ip
		pr.request_name = requestName
		pr.request_type = None
		pr.poison_name = poisonName
		pr.poison_addr = poisonIP
		pr.mode = self.settings['mode']

		self.logQ.put(pr)

	def logEmail(self, emailEntry):
		self.log('You got mail!', logging.INFO)
		self.logQ.put(emailEntry)

	def logProxy(self, data, laddr, raddr, level = logging.INFO):
		message = '[%s -> %s] %s' % ('%s:%d' % laddr, '%s:%d' % raddr, data)
		self.logQ.put(LogEntry(level, self.modulename, message))

	def logProxyData(self, data, laddr, raddr, isSSL, datatype):
		pd = ProxyData()
		pd.src_addr  = laddr
		pd.dst_addr  = raddr
		pd.proto     = self.protocol
		pd.isSSL     = isSSL
		pd.data_type = datatype
		pd.data      = data

		self.logQ.put(pd)

	def logexception(self, message = None):
		sio = io.StringIO()
		ei = sys.exc_info()
		tb = ei[2]
		traceback.print_exception(ei[0], ei[1], tb, None, sio)
		msg = sio.getvalue()
		if msg[-1] == '\n':
			msg = msg[:-1]
		sio.close()
		if message is not None:
			msg = message + msg
		self.log(msg, level=logging.ERROR)
