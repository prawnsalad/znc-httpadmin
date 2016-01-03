# znc-httpadmin
Administer ZNC via HTTP requests

##### Requires
* ZNC 1.6.0+
* modpython

##### API functions
Each function is called via basic HTTP GET requests to ZNC. As httpadmin is loaded as a global module the base path for all API calls will be `/mods/global/httpadmin/`. Parameters are passed via the querystring.

	/adduser              (username, password)
	/deluser              (username)
	/userpassword         (username, password)
	/addnetwork           (username, net_name, net_addr, net_port, [net_pass, net_ssl])
	/delnetwork           (username, net_name)
	/listnetworks         (username)

	/networkconnect       (username, net_name)
	/networkdisconnect    (username, net_name)
