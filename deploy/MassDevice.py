#For Python 2.7

import json
import subprocess
from threading import Timer
import threading
import time
from datetime import datetime
import socket
import select
import string
import sys
import ws4py
import signal
import os
import traceback
from ws4py.client.threadedclient import WebSocketClient
#===================================
#             Settings:
#===================================
#Minimum time between updates sent (in seconds)
updateRate = 1
#Human-Friendly device identifier
ustring = "Device running the MassManager Script."
#Change server address (and port)
server_address = "ws://192.168.2.232:80/csock"
#===================================
#           End Settings
#===================================


reconnect = 1
next_ID = 1
commands = {}
wsock = None
conn_open = False
stop = False
class SystemStats():
    c=[]
    h=""
    i4=""
    i6=""
    d=""
    t=""
    u=""
    s=""
    df=""
    du=""


class CmdHolder(threading.Thread):
    process = None
    id = -1
    cmd = ""
    buf = ""
    sendLock = threading.Lock()
    def send_output(self, id, text):
        global wsock
        #TODO: Implement buffering and batching to save on overhead.
        self.sendLock.acquire()
        c = []
        self.buf += text
        c.append(id)
        c.append(self.buf)
        try:
            global conn_open
            if conn_open:
                wsock.send("OUT:" + json.dumps(c))
                self.buf = ""
                self.sendLock.release()
                return 0
            else:
                #This exception is just here so that I can reuse the "except" statement.
                #it wouldn't matter what I put, even if it was FoodException("Line 42: Unexpected Waffle, was expecting Carrot")
                raise Exception("Sending failed: Socket is no longer open.")
        except:
            self.sendLock.release()
            return 1
    def send_sigint(self):
        try:
            self.send_output(self.id, "\n======\nSIGINT\n======\n")
            os.killpg(self.process.pid, signal.SIGINT)

        except:
            self.send_output(self.id, "Failed to send SIGINT.")
    def __init__(self, cmd):
        threading.Thread.__init__(self)
        global next_ID
        self.id = next_ID
        self.cmd = cmd
        
    def run(self):
        self.process = subprocess.Popen(self.cmd, shell=True, stderr = subprocess.STDOUT, stdout = subprocess.PIPE, stdin = subprocess.PIPE, preexec_fn=os.setsid)
        while self.process.poll() == None:
            #live updates as the command executes
            out = self.process.stdout.readline()
            if out is not None:
                self.send_output(self.id, out)
        #send any unread output
        out = self.process.stdout.read()
        if out is not None:
            self.send_output(self.id, out)
        while self.send_output(self.id, ""):
            time.sleep(0.1)

class DeviceClient(WebSocketClient):
    global conn_open
    authStatus = "?"
    hName = subprocess.check_output("hostname")[:-1]
    tim = None

    def run_command(self, cmd):
        global next_ID
        commands[next_ID] = CmdHolder(cmd)
        commands[next_ID].start()
        next_ID += 1
    def do_update(self):
        jsonFile = prepare_update()
        try:
            self.send("STA:" + jsonFile)
            self.tim = Timer(updateRate, self.do_update).start()
        except:
            print "Couldn't send data."
            try:
                self.close()
            except:
                pass
    def opened(self):
        print "Connected."
        global conn_open 
        conn_open = True
        self.send("DEV:" + self.hName)
    def closed(self, code, reason=None):
        conn_open = False
        try:
            print "Disconnected."
            self.tim.cancel()
        except:
            pass
        print reason
    def received_message(self, message):
        if self.authStatus == "?":
            if message.data == "OK":
                self.authStatus = "OK"
                self.tim = Timer(updateRate, self.do_update).start()
            else:
                raise Exception("Server did not reply with OK when expected.")
        elif self.authStatus == "OK":
            msg = string.split(message.data, ":", 1)
            if msg[0]=="CMD":
                self.run_command(msg[1])
            if msg[0]=="SIGINT":
                try:
                    commands[int(msg[1])].send_sigint()
                except KeyError:
                    c = []
                    c.append((msg[1], "Failed to send SIGINT: Process does not exist"))
                    self.send("OUT:" + json.dumps(c))

def prepare_update():
    stats = SystemStats()
    stats.s=ustring
    stats.h=subprocess.check_output("""hostname""")[:-1]
    #Using ip instead of ifconfig because different configurations of ifconfig can actually change the output, which ruins this script.
    #TODO: Quit using awk and parse the outputs inside the script for faster performance and better portability.
    stats.i4=subprocess.check_output("""/sbin/ip -o -4 addr list eth0 | awk '{print $4}' | cut -d/ -f1""",shell=True)[:-1]
    stats.i6=subprocess.check_output("""/sbin/ip -o -6 addr list eth0 | awk '{print $4}' | cut -d/ -f1""",shell=True)[:-1]
    stats.d=subprocess.check_output("""date +"%Y/%m/%d %T" """, shell=True)[:-1]
    stats.t=subprocess.check_output("""/opt/vc/bin/vcgencmd measure_temp | awk -F "[=']" '{print $2}'""",shell=True)[:-1]
    stats.u=subprocess.check_output("""cat /proc/uptime | awk -F " " '{print $1}'""",shell=True)[:-1]
    #Disk Stats:
    disk = subprocess.check_output("""df /""", shell=True)
    disk = disk.splitlines()[1]
    disk = disk.split(" ")
    disk = filter(None, disk)
    stats.du=disk[2]
    stats.df=disk[3]
    return json.dumps(stats.__dict__)

def start_connection():
    global reconnect
    global stop
    global wsock
    hostname = subprocess.check_output("hostname")[:-1]
    #if the connection was still open, we're closing it.
    try:
        wsock.close()
    except:
        #and if it wasn't, it's no big deal.
        pass
    while True:
        try:
            print "Connecting..."
            wsock = DeviceClient(server_address)
            wsock.connect()
            wsock.run_forever()
        except KeyboardInterrupt:
            print "Interrupt received, exiting now."
            break
        except:
            print ("Failed to connect to server: " + server_address)
    
def main():
    start_connection()
main()