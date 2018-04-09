# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from operator import attregetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import in_proto
from ryu.lib import hub

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
    	datapath = ev.datapath
    	if ev.state == MAIN_DISPATCHER
    	    if not datapath.id in self.datapaths:
    	    	self.logger.debug('register datapath: %016x', datapath.id)
    	    	self.datapaths[datapath.id] = datapath
    	   elif ev.state is DEAD_DISPATCHER:
    	   		if datapath.id in self.datapaths:
    	   			self.logger.debug('unregister datapath: %016x', datapath.id)
    	    		self.datapaths[datapath.id] = datapath
    
    def _monitor(self):
    	while True:
    		for value in self.datapaths.values():
    			self.request_states(value)
    		hub.sleep(10)

    def _request_state(self, datapath):
    	self.logger.debug('send states request: %016x', datapath.id)
    	ofproto = datapath.ofproto
    	parser = datapath.ofproto_parser

    	request = parser.OFPFlowStatsRequest(datapath)
    	datapath.send_msg(request)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
    	body = ev.msg.body

    	self.logger.info('datapath        '
    		             'in-port    eth-dst            '
    		             'out-port   packets    bytes')
    	self.logger.info('---------------------'
    					 '-------------------------------'
    					 '-------------------------------')
    	for stat in sorted([flow for flow in body if flow.priority == 1],
    		               key=lambda flow: (flow.match['in_port'],
    		               	                  flow.match['eth_dst'])):
    		self.logger.info('%016x %8x %17s %8x %8d %8d',
    			             ev.msg.datapath.id,
    			             stat.match['in_port'], stat.match['eth_dst'],
    			             stat.instructions[0].actions[0].port,
    			             stat.packet_count, stat.byte_count)





    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        
		
		###########################################################################
        if pkt.get_protocol(arp.arp):
            print("Arp")
            arp_pkt = pkt.get_protocol(arp.arp)
            arp_src = arp_pkt.src_ip
            arp_dst = arp_pkt.dst_ip
            #print("arp src_ip %s"%arp_pkt.src_ip)
            #print("arp dst_ip %s"%arp_pkt.dst_ip)
            #block_host = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS,[])] 
            block_host = [] #empty action set ==> by default will drop packet
            
            if (arp_src=='10.0.0.2' and arp_dst=='10.0.0.3'):
                print("pkt blocked from 10.0.0.2 t0 10.0.0.3")
                arp_match1 = parser.OFPMatch(in_port=in_port, eth_type = 0x0806, arp_tpa=arp_dst, arp_spa=arp_src)
                self.add_flow(datapath, 1, arp_match1, block_host, msg.buffer_id)
                print("Flow added")
                
            elif (arp_src=='10.0.0.3' and arp_dst=='10.0.0.2') :
                print("pkt blocked from 10.0.0.3 t0 10.0.0.2")
                arp_match2 = parser.OFPMatch(in_port=in_port, eth_type = 0x0806, arp_tpa=arp_dst, arp_spa=arp_src)
                self.add_flow(datapath, 1, arp_match2, block_host, msg.buffer_id)
                print("Flow added")     
                '''
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=block_host, data=data)
                datapath.send_msg(out)
                '''
                return      
		###########################################################################
		
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        
   
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match    = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
         
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)