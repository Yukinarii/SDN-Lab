from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import logging
import os

logging.basicConfig(filename='./fattree.log', level=logging.INFO)
logger = logging.getLogger(__name__)


class Fattree(Topo):
    logger.debug("Class Fattree")
    CoreSwitchList = []
    AggSwitchList = []
    EdgeSwitchList = []
    HostList = []

    def __init__(self, k):
        logger.debug("Class Fattree init")
        self.pod = k
        self.iCoreLayerSwitch = (k/2)**2
        self.iAggLayerSwitch = k*(k/2)
        self.iEdgeLayerSwitch = k*(k/2)
        self.iHost = self.iEdgeLayerSwitch * (k/2)

        #Init Topo
        Topo.__init__(self)

    def createTopo(self):
        self.createCoreLayerSwitch(self.iCoreLayerSwitch)
        self.createAggLayerSwitch(self.iAggLayerSwitch)
        self.createEdgeLayerSwitch(self.iEdgeLayerSwitch)
        self.createHost(self.iHost)

    """
    Create Switch and Host
    """

    def _addSwitch(self, number, layer, switch_list):
        for x in xrange(1, number+1):
            PREFIX = str(layer) + "00"
            if x >= int(10):
                PREFIX = str(layer) + "0"
            switch_list.append(self.addSwitch(PREFIX + str(x)))

    def createCoreLayerSwitch(self, number):
        logger.debug("Create Core Layer")
        self._addSwitch(number, 1, self.CoreSwitchList)

    def createAggLayerSwitch(self, number):
        logger.debug("Create Agg Layer")
        self._addSwitch(number, 2, self.AggSwitchList)

    def createEdgeLayerSwitch(self, number):
        logger.debug("Create Edge Layer")
        self._addSwitch(number, 3, self.EdgeSwitchList)

    def createHost(self, number):
        logger.debug("Create Host")
        for x in xrange(1, number+1):
            PREFIX = "h00"
            if x >= int(10):
                PREFIX = "h0"
            elif x >= int(100):
                PREFIX = "h"
            self.HostList.append(self.addHost(PREFIX + str(x)))

    """
    Add Link
    """
    def createLink(self):
        logger.debug("Add link Core to Agg.")
        end = self.pod / 2
        for x in xrange(0, self.iAggLayerSwitch, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.addLink(
                        self.CoreSwitchList[i*end+j],
                        self.AggSwitchList[x+i],
                        bw=1000, loss = 2)

        logger.debug("Add link Agg to Edge.")
        for x in xrange(0, self.iAggLayerSwitch, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.addLink(
                        self.AggSwitchList[x+i], self.EdgeSwitchList[x+j],
                        bw=100)

        logger.debug("Add link Edge to Host.")
        for x in xrange(0, self.iEdgeLayerSwitch):
            for i in xrange(0, self.pod / 2):  #each edge switch connect to k/2 hosts
                self.addLink(
                    self.EdgeSwitchList[x],
                    self.HostList[self.pod / 2 * x + i],
                    bw=100)

    def set_ovs_stp(self,):
        self._set_ovs_stp(self.CoreSwitchList)
        self._set_ovs_stp(self.AggSwitchList)
        self._set_ovs_stp(self.EdgeSwitchList)

    def _set_ovs_stp(self, sw_list):
            for sw in sw_list:
                cmd = "sudo ovs-vsctl set bridge %s stp_enable=true" % sw
                os.system(cmd)


def iperfTest(net, topo):
    logger.debug("Start iperfTEST")
    h1000, h1001, h1016 = net.get(
        topo.HostList[0], topo.HostList[1], topo.HostList[15])

    #iperf Server
    h1000.popen(
        'iperf -s -u -i 1 > iperf_server_differentPod_result', shell=True)

    #iperf Server
    h1016.popen(
        'iperf -s -u -i 1 > iperf_server_samePod_result', shell=True)

    #iperf Client
    h1001.cmdPrint('iperf -c ' + h1000.IP() + ' -u -t 10 -i 1 -b 100m')
    h1001.cmdPrint('iperf -c ' + h1016.IP() + ' -u -t 10 -i 1 -b 100m')


def pingTest(net):
    logger.debug("Start Test all network")
    net.pingAll()


def createTopo(pod, ip="10.0.2.15", port=6653):
    logging.debug("LV1 Create Fattree")
    topo = Fattree(pod)
    topo.createTopo()
    topo.createLink()

    logging.debug("LV1 Start Mininet")
    CONTROLLER_IP = ip
    CONTROLLER_PORT = port
    net = Mininet(topo=topo, link=TCLink, controller=None, autoSetMacs=True,
                  autoStaticArp=True)
    net.addController(
        'controller', controller=RemoteController,
        ip=CONTROLLER_IP, port=CONTROLLER_PORT)
    net.start()

    #topo.set_ovs_stp()

    logger.debug("LV1 dumpNode")

    dumpNodeConnections(net.hosts)
    pingTest(net)
    iperfTest(net, topo)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createTopo(4)

"""
reference :
https://gist.github.com/pichuang/9875468
https://www.cs.cornell.edu/courses/cs5413/2014fa/lectures/08-fattree.pdf
"""
