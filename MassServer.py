import time
import string
import json
import cherrypy
import ws4py
import os
import inspect
import threading
import socket
import SocketServer
import sys, traceback
import csv
import pages
import math
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

STATS_KEYS = ['h','i4','i6','d','t','u','s','df','du']
MAX_LOG_SIZE = 52992

def sendThread(sockobj, message):
    global deviceContainer
    try:
        sockobj.send(message)
    except:
        pass
        
#A new copy of this object is instantiated for each socket connection created.
class ClientSocket(WebSocket):
    continueloop = True
    target = ""
    usertype = "?"
    inUse = False
    def opened(self):
        print "Socket Opened."
        
    def received_message(self, message):
        global deviceContainer
        try:
            if self.usertype == "?":
                msg = string.split(message.data, ":")
                if msg[0]=="MON":
                    self.target = msg[1]
                    self.usertype = "MON"
                    self.send("OK")
                    #deviceContainer.add_sub(self, self.target)
                if msg[0]=="DEV":
                    self.usertype = "DEV"
                    self.target = msg[1]
                    self.send("OK")
                    deviceContainer.register_socket(self.target, self)
                    deviceContainer.add_cmd_entry(msg[1])
            elif self.usertype == "MON":
                msg = string.split(message.data, ":", 1)
                #ADD REM and CLR will be used if/when I work on displaying multiple devices at once.
                if msg[0] == "LST":
                    self.send("LST:" + json.dumps(list(deviceContainer.devices.keys())))
                elif msg[0] == "LSS":
                    c = {}
                    for entry in deviceContainer.dicts:
                        pass
                elif msg[0] == "ADD":
                    deviceContainer.add_sub(self, msg[1])
                elif msg[0] == "REM":
                    deviceContainer.rem_sub(self, msg[1])
                elif msg[0] == "CLR":
                    deviceContainer.clear_client(self)
                elif msg[0] == "SIGINT":
                    print "SIGINT"
                    msg = string.split(message.data, ":", 2)
                    if deviceContainer.send_raw("SIGINT:" + msg[2], msg[1]) == 1:
                        c = []
                        c.append((msg[2], "Server: Could not send SIGINT.\n"))
                        self.send("OUT:" + json.dumps(c))
                elif msg[0] == "CMD":
                    msg = string.split(message.data, ":", 2)
                    tgts = msg[1].split(";")
                    for target in tgts:
                        deviceContainer.add_sub(self, target)
                        result = deviceContainer.send_command(msg[2], target)
                        if result == 1:
                            c = [0, "Server", "Device does not exist: " + target + "\n"]
                            self.send("OUT:" + json.dumps(c))
                        elif result == 2:
                            c = [0, "Server", "Device not connected: " + target + "\n"]
                            self.send("OUT:" + json.dumps(c))
                    
            elif self.usertype == "DEV":
                msg = string.split(message.data, ":", 1)
                if msg[0] == "STA":
                    deviceContainer.update_device(msg[1])
                if msg[0] == "OUT":
                    d = json.loads(msg[1])
                    d.insert(1, self.target)
                    outJson = json.dumps(d)
                    deviceContainer.push_to_subs("OUT:" + outJson, self.target)
                    pass
        except Exception as e:
            print "Exception occurred on received message:"
            traceback.print_exc(file=sys.stdout)
    def closed(self, code, reason):
        continueloop = False
        if self.usertype == "MON":
            deviceContainer.clear_client(self)
        if self.usertype == "DEV":
            deviceContainer.unregister_socket(self.target)
    def update_ready(self, message):
        thread = threading.Thread(target = sendThread, args = (self, message))
        thread.start()
def always_two_digit(startNum):
    num = int(startNum)
    if (num < 10 and num >= 0):
        return "0"+str(num)
    else:
        return str(num)

def format_uptime(startTime):
    upRem = startTime
    upDays = math.floor(upRem / 86400)
    upRem -= upDays * 86400
    upHours = math.floor(upRem / 3600)
    upRem -= upHours * 3600
    upMins = math.floor(upRem / 60);
    upRem -= upMins * 60
    upSecs = math.floor(upRem)
    fDays = always_two_digit(upDays)
    fHours = always_two_digit(upHours)
    fMins = always_two_digit(upMins)
    fSecs = always_two_digit(upSecs)
    return fDays + "d" + fHours + "h" + fMins + "m" + fSecs + "s"
def format_storage(num):
    return "%.2f" % (num/1048576) + " GB"
class Sockdir(object):
        @cherrypy.expose
        def csock(self):
            pass
        @cherrypy.expose
        def stats(self, device=None):
            if (device==None):
                return pages.noDevice
            else:
                rawsts = deviceContainer.dicts[device]
                sts = {}
                page = pages.statsPage
                #Add blank entries if any are missing (say, due to outdated software on the device)
                for key in STATS_KEYS:
                    try:
                        sts[key] = rawsts[key]
                    except:
                        sts[key] = ""
                #if the keys were missing these will throw ValueError. If so, fill with placeholder data.
                try:
                    utime = format_uptime(int(float(sts['u'])))
                except:
                    utime = format_uptime(0)
                try:
                    dfree = format_storage(float(sts['df']))
                except:
                    dfree = format_storage(0)
                try:
                    dused = format_storage(float(sts['du']))
                except:
                    dused = format_storage(0)
                newPage = page.format(
                    DeviceName=sts['h'],
                    IPV4 = sts['i4'],
                    IPV6 = sts['i6'],
                    UString = sts['s'],
                    LastUpdate = sts['d'],
                    Temp = sts['t'] + "&deg;C",
                    Uptime = utime,
                    FreeDisk = dfree,
                    UsedDisk = dused)
                return newPage
                
def sanitizeDate(raw):
    new = raw.replace('/', '-')
    new = new.replace(':', '-')
    return new
class DeviceContainer(object):
    devices = {}
    dicts = {}
    subscribers = {}
    terms = {}
    termsubs = {}
    commands = {}
    sockets = {}
    devicedir = os.getcwd() + "\\devices"
    def register_socket(self, target, socket):
        self.sockets[target] = socket
    def unregister_socket(self, target):
        self.sockets[target] = None
    def add_sub_entry(self, target):
        try:
            self.subscribers[target] == None
        except KeyError:
            self.subscribers[target] = []
    def add_cmd_entry(self, target):
        try:
            self.commands[target] == None
        except KeyError:
            self.commands[target] = []
    def populate_devices(self):
        for f in os.listdir(self.devicedir):
            if string.split(f, ".")[-1] == "json":
                jsonFile = open(self.devicedir +"\\"+ f, "rb")
                rawData = jsonFile.read()
                jsonDict = json.loads(rawData)
                name = jsonDict['h']
                self.dicts[name] = jsonDict
                self.devices[name] = rawData
                self.add_sub_entry(name)
    def add_sub(self, client, target):
        try:
            #Check if the client is already in the list.
            #If so, the code succeeds and returns.
            #If not, the ValueError thrown lets us know they're
            #not on the list.
            self.subscribers[target].index(client)
            return 0
        except ValueError:
            self.subscribers[target].append(client)
            client.update_ready("STA:" + self.devices[target])
            return 1
        except KeyError:
            print "client attempted to subscribe to a device that does not exist."
    def send_command(self, cmd, target):
        if target in self.sockets:
            if self.sockets[target] is not None:
                self.sockets[target].send("CMD:" + cmd)
            else:
                return 2
        else:
            return 1
    def send_raw(self, data, target):
        if target in self.sockets and self.sockets[target] is not None:
            self.sockets[target].send(data)
        else:
            return 1
    def rem_sub(self, client, target):
        try:
            i = self.subscribers[target].index(client)
            self.subscribers[target].pop(i)
            return 1
        except ValueError:
            return 0
    def clear_client(self, client):
        for entry in self.subscribers:
            try:
                i = self.subscribers[entry].index(client)
                self.subscribers[entry].pop(i)
            except ValueError:
                pass 
    def push_to_subs(self, data, target):
        for client in self.subscribers[target]:
            client.update_ready(data)
    def update_device(self, data):
        jsonDict = json.loads(data)
        name = jsonDict['h']
        filedir = os.getcwd() + "/devices/logs/" + os.path.basename(name) + '/'
        self.dicts[name] = jsonDict
        self.devices[name] = data
        jsonFile = open(os.getcwd() + "/devices/" + os.path.basename(name) + ".json", "wb")
        jsonFile.write(data)
        jsonFile.close()
        if not os.path.exists('devices/logs/' + name + '/'):
            os.makedirs('devices/logs/' + name + '/')
        if os.path.getsize(filedir + "current.csv") > MAX_LOG_SIZE:
            try:
                csvfile = open(filedir + "current.csv")
                reader = csv.reader(csvfile)
                first = sanitizeDate(reader.next()[0])
                csvfile.close()
                os.rename(filedir + "current.csv", filedir + first + ".csv")
            except:
                traceback.print_exc(file=sys.stdout)
        with open(filedir + "current.csv", "ab+") as csvfile:
            logwriter = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            logwriter.writerow([jsonDict['d'], jsonDict['t']])
        self.add_sub_entry(name)
        self.push_to_subs("STA:" + data, name)
cherrypy.config.update({'server.socket_port': 80})
cherrypy.config.update({'server.socket_host': "0.0.0.0"})
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()
app = cherrypy.tree.mount(Sockdir(), "/", config={'/csock': {'tools.websocket.on': True, 'tools.websocket.handler_cls': ClientSocket}})
app.merge("server.conf")
deviceContainer = DeviceContainer()
deviceContainer.populate_devices()
cherrypy.engine.start()
cherrypy.engine.block()
