#MassManager Device

##Setup

Edit the script and change the following settings to fit your needs: 

updateRate: Minimal time in seconds between sending updates to the server

ustring: Human-Friendly string to identify the device (can be left blank)

server_address: WebSocket address to the server you're running.

##Notes

This script was originally written for the Raspberry Pi.
It fetches the output from a number of shell commands 
to gather information on the device. Some of these commands
may be different on the device you're using. If so, you can safely change
the strings seen in the function prepare_update, however keep in mind that
you will need to preserve the formatting the server expects, else things
will look odd.

##Security Concerns

This system lets you run arbitrary shell commands on devices.
Don't be stupid. Authentication and encryption are yet to be implemented,
so make sure that devices are running on a VPN or an otherwise trusted
connection.