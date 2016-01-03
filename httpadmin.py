"""

Response formats (via the response query string value):
	response=json     JSON encoded
	response=pairs    Key+Value pairs


API HTTP root (once loaded into ZNC as a global module):
	/mods/global/httpadmin/


API functions:
	/adduser              (username, password)
	/deluser              (username)
	/userpassword         (username, password)
	/addnetwork           (username, net_name, net_addr, net_port, [net_pass, net_ssl])
	/delnetwork           (username, net_name)
	/listnetworks         (username)

	/networkconnect       (username, net_name)
	/networkdisconnect    (username, net_name)

"""


import znc
import json

class httpadmin(znc.Module):
	module_types = [znc.CModInfo.GlobalModule]

	description = "HTTP admin interface to ZNC"

	user_cache = {}
	network_cache = {}


	def OnLoad(self, args, message):
		return True



	def GetUser(self, username):
		if (username in self.user_cache):
			user = self.user_cache[username]
		else:
			user = znc.CZNC.Get().FindUser(username)

			if (user):
				self.user_cache[username] = user

		return user


	def GetNetwork(self, username, net_name):
		key = username + "-" + net_name
		if (key in self.network_cache):
			return self.network_cache[key]

		user = self.GetUser(username)
		if (not user):
			return False

		network = user.FindNetwork(net_name)
		if (not network):
			return False

		self.network_cache[key] = network
		return network



	def OnWebPreRequest(self, WebSock, sPageName):
		if (not WebSock.GetSession().IsAdmin()):
			WebSock.PrintErrorPage(403, "Forbidden", "You need to be an admin to access this page");
			return True

		ret = {"error": "unknown_method"}
		action = sPageName

		if (action == "adduser"):
			ret = self.ApiAddUser(WebSock)

		elif (action == "deluser"):
			ret = self.ApiDelUser(WebSock)

		elif (action == "userpassword"):
			ret = self.ApiUserPassword(WebSock)

		elif (action == "addnetwork"):
			ret = self.ApiAddNetwork(WebSock)

		elif (action == "delnetwork"):
			ret = self.ApiDelNetwork(WebSock)

		elif (action == "listnetworks"):
			ret = self.ApiListNetworks(WebSock)

		elif (action == "networkconnect"):
			ret = self.ApiNetworkConnect(WebSock)

		elif (action == "networkdisconnect"):
			ret = self.ApiNetworkDisconnect(WebSock)


		response_format = WebSock.GetParam("response", False)
		if (not response_format):
			response_format = "json"

		response_text = ""

		if (ret and response_format == "json"):
			response_text = json.dumps(ret, separators=(',', ':'))

		elif (ret and response_format == "pairs"):
			for key in ret.keys():
				response_text += key + "=" + str(ret[key]) + ", "

		WebSock.PrintHeader(len(response_text))
		WebSock.Write(response_text)
		WebSock.Close(znc.Csock.CLT_AFTERWRITE)

		return True



	def ApiAddUser(self, WebSock):
		username = WebSock.GetParam("username", False)
		password = WebSock.GetParam("password", False)

		if (username == "" or password == ""):
			return {"error": "invalid_params"}

		salt = znc.CUtils.GetSalt()
		hash = znc.CUser.SaltedHash(password, salt)

		new_user = znc.CUser(username)
		new_user.SetPass(hash, znc.CUser.HASH_DEFAULT, salt)

		str_err = znc.String()
		if (znc.CZNC.Get().AddUser(new_user, str_err) == False):
			return {"error": "error_adding_user", "description": str_err.s}

		# Cache the user to get around python deleting the user again
		# https://github.com/znc/znc/issues/462#issuecomment-32209823
		self.user_cache[username] = new_user
		znc.CZNC.Get().WriteConfig()

		return {"error": False}



	def ApiDelUser(self, WebSock):
		username = WebSock.GetParam("username", False)

		if (username == "" ):
			return {"error": "invalid_params"}

		user = self.GetUser(username)
		if (not user):
			return {"error": "user_not_exists"}

		if (znc.CZNC.Get().DeleteUser(username) == False):
			return {"error": "error_deleting_user"}

		# Cache the user to get around python deleting the user again
		# https://github.com/znc/znc/issues/462#issuecomment-32209823
		if (self.user_cache[username]):
			del self.user_cache[username]

		znc.CZNC.Get().WriteConfig()

		return {"error": False}



	def ApiUserPassword(self, WebSock):
		username = WebSock.GetParam("username", False)
		password = WebSock.GetParam("password", False)

		if (username == "" or password == ""):
			return {"error": "invalid_params"}

		user = self.GetUser(username)
		if (not user):
			return {"error": "user_not_found"}

		salt = znc.CUtils.GetSalt()
		hash = znc.CUser.SaltedHash(password, salt)
		user.SetPass(hash, znc.CUser.HASH_DEFAULT, salt)

		znc.CZNC.Get().WriteConfig()

		return {"error": False}



	def ApiAddNetwork(self, WebSock):
		username = WebSock.GetParam("username", False)
		net_name = WebSock.GetParam("net_name", False)
		net_addr = WebSock.GetParam("net_addr", False)
		net_port = int(WebSock.GetParam("net_port", False))
		net_pass = WebSock.GetParam("net_pass", False)

		if (WebSock.GetParam("net_ssl", False) == "1"):
			net_ssl = True
		else:
			net_ssl = False

		user = self.GetUser(username)

		if (user.HasSpaceForNewNetwork() == False):
			return {"error": "limit_reached"}

		network = user.FindNetwork(net_name)
		if (network):
			return {"error": "network_exists"}

		network = znc.CIRCNetwork(user, net_name)
		user.AddNetwork(network)

		success = network.AddServer(net_addr, net_port, net_pass, net_ssl)
		if (success == False):
			return {"error": "error_adding_network"}

		self.network_cache[username + "-" + net_name] = network
		znc.CZNC.Get().WriteConfig()

		return {"error": False}



	def ApiDelNetwork(self, WebSock):
		username = WebSock.GetParam("username", False)
		net_name = WebSock.GetParam("net_name", False)

		if (username == "" or net_name == ""):
			return {"error": "invalid_params"}

		user = self.GetUser(username)
		if (not user):
			return {"error": "user_not_found"}

		user.DeleteNetwork(net_name)

		znc.CZNC.Get().WriteConfig()

		if (self.network_cache[username + "-" + net_name]):
			del self.network_cache[username + "-" + net_name]

		return {"error": False}



	def ApiListNetworks(self, WebSock):
		username = WebSock.GetParam("username", False)

		if (username == ""):
			return {"error": "invalid_params"}

		user = self.GetUser(username)
		if (not user):
			return {"error": "user_not_found"}

		networks = []
		user_networks = user.GetNetworks()
		for network in user_networks:
			server = network.GetCurrentServer()
			if (server):
				server_name = server.GetName()
			else:
				server_name = ""

			networks.append({
				"name": network.GetName(),
				"server": server_name,
				"connected": network.IsIRCConnected()
			})

		return {"error": False, "networks": networks}



	def ApiNetworkConnect(self, WebSock):
		username = WebSock.GetParam("username", False)
		net_name = WebSock.GetParam("net_name", False)

		if (username == "" or net_name == ""):
			return {"error": "invalid_params"}

		network = self.GetNetwork(username, net_name)
		if (not network):
			return {"error": "network_not_found"}

		network.SetIRCConnectEnabled(True)

		return {"error": False}



	def ApiNetworkDisconnect(self, WebSock):
		username = WebSock.GetParam("username", False)
		net_name = WebSock.GetParam("net_name", False)

		if (username == "" or net_name == ""):
			return {"error": "invalid_params"}

		network = self.GetNetwork(username, net_name)
		if (not network):
			return {"error": "network_not_found"}

		network.SetIRCConnectEnabled(False)

		return {"error": False}

