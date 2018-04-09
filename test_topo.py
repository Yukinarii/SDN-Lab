#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.cli import CLI
import os
import time

class MyTopo( Topo ):
	#Simple topology example.
	Switches = []
	Hosts    = []

	def __init__(self):

		#init topo
		Topo.__init__(self)

	def create_init(self):
		self.createtopo()

	def createtopo(self):
		#create switches and hosts
		
		#Switches
		self.Switches.append(self.addSwitch('s1001'))
		self.Switches.append(self.addSwitch('s2001'))
		self.Switches.append(self.addSwitch('s2002'))
		
		#Hosts
		self.Hosts.append(self.addHost('h3001'))
		self.Hosts.append(self.addHost('h3002'))
		self.Hosts.append(self.addHost('h3003'))
		self.Hosts.append(self.addHost('h3004'))

	def createlinks(self):
		###Add links###
		self.addLink(self.Switches[0],self.Switches[1])
		self.addLink(self.Switches[0],self.Switches[2])
		self.addLink(self.Switches[1],self.Hosts[0])
		self.addLink(self.Switches[1],self.Hosts[1])
		self.addLink(self.Switches[2],self.Hosts[2])
		self.addLink(self.Switches[2],self.Hosts[3])
		
						
	def enable_ISP_OpenFlow(self):
	
		for sw in self.Switches:
			cmd = "sudo ovs-vsctl set bridge %s stp_enable=true" % sw
			os.system(cmd)
			print(cmd)
			cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
			os.system(cmd)
			print(cmd)

		
def emul_start():
	"Crerate network and run simple performance test"
	topo = MyTopo()
	print("Create topo...")
	topo.create_init() #create topology
	print("Create links...")
	topo.createlinks() #create links
	topo.enable_ISP_OpenFlow()
	
	###******###
	net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True) #autosetmac will let the MAC of switches be in order
	###******###
	
	#net = Mininet(topo=topo, link=TCLink, autoSetMacs=True)
	#print("Add controller...")
	net.addController('controller', controller=RemoteController, ip="10.0.2.15", port=6653)	
	net.start() #start Mininet
	net.pingAll() #do pingall test
	CLI(net) #for debugging
	net.stop() # stop Mininet

if __name__ == '__main__':
	# Set log level
	# you can use 'info', 'warning', 'critical', 'error', 'debug', 'output'
	setLogLevel('info')
	emul_start()
	
