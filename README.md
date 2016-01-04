# znc-httpadmin
Administer ZNC via HTTP requests

##### Requires
* ZNC 1.6.0+
* modpython

##### API functions
Each function is called via basic HTTP GET requests to ZNC. As httpadmin is loaded as a global module the base path for all API calls will be `/mods/global/httpadmin/`. Parameters are passed via the querystring. Responses will be in JSON form.

	/adduser              (username, password)
	/deluser              (username)
	/userpassword         (username, password)
	/addnetwork           (username, net_name, net_addr, net_port, [net_pass, net_ssl])
	/delnetwork           (username, net_name)
	/listnetworks         (username)

	/networkconnect       (username, net_name)
	/networkdisconnect    (username, net_name)

##### Authentication
All API requests must be logged into ZNC as an admin user. You can pass the admins username and password by using HTTP Basic Auth. An example using curl with this would be: `$ curl --user admin:1234 "http://127.0.0.1:3000/mods/global/httpadmin/adduser?username=prawnsalad&password=mypassword`
