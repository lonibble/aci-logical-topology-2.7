#
# Script to read output from pb-logical-topology.yml and create nice output.
#
# To Do's
# - Try to send the output by e-mail
#
#####################
# Imports
#####################
#
# list of packages that should be imported for this code to work
import re
import pdb
import json
import copy
import inspect
from pprint import pprint
import xlsxwriter
# import time
# import ipaddress
import sys
import argparse

######################################
# Classes
######################################
#
class MyAciObjects(object):
    '''
    A class representing an generic object
    '''
    # Class Attributes ##################
    # Methods #####################
    def __init__(self, name =  '', desc = '', dn = '', tenant = ''):
        self.name = name
        self.desc = desc
        self.dn = dn
        self.tenant = tenant

    def __str__(self):
        return "Name ["+self.name+"], Description ["+self.desc+"]"

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "{:_<15}: {}\n".format("Distinguished Name", self.dn)
        out_string += indent + "{:_<15}: {}\n".format("Tenant", self.tenant)
        return out_string

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'AciObjects'

    def setName(self, name):
        ''' Sets Object's name to name '''
        self.name = name

    def getName(self):
        ''' Returns the Object's name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the Object's description to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the Object's description as a string '''
        return str(self.desc)

    def setDn(self, dn):
        ''' Sets the Object's dn to dn '''
        self.dn = dn

    def getDn(self):
        ''' Returns the Object's DN as a string '''
        return str(self.dn)

    def getTenant(self):
        ''' Returns the Tenant name based on the DN '''
        tenant = 'Error getting tenant name from DN'
        m = re.search('^\uni\/(.+)\/.*$', self.dn)
        if m:
            tenant = m.group(1)
        return tenant

    def getTenantDn(self):
        ''' Returns the Tenant name based on the DN '''
        tenant = 'Error getting tenant name from DN'
        m = re.search('^(.+)\/.*$', self.dn)
        if m:
            tenant = m.group(1)
        return tenant

    def getDefaultName(self, cust, index):
        ''' Returns a Object's proposed default name as a string '''
        # return "{:_<10}_{:02d}".format(cust, index)
        return "{:_<10}_{:02d}".format(self.getType(), index)

    def getBasicData(self, project_desc, cust, index):
        name = collect_string_input('Name: ', 1, 14, default_value = self.getDefaultName(cust, index))
        desc = collect_string_input('Description: ', 1, 60, default_value = project_desc)
        self.setName(name)
        self.setDesc(self.getType() + ": " + desc)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
# end of class MyAciObjects

class MyTenant(MyAciObjects):
    '''
    A class representing a tenant
    '''
    # Class Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.vrfs = {}
        self.aps = {}
        self.l3outs = {}

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'Tenant'

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("Tenant Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "VRFs:" + "\n"
        for vrf in self.vrfs:
            out_string += vrf.pretty_output(indent_level+1) + "\n"

        out_string += indent + "APs:" + "\n"
        for ap in self.aps:
            out_string += ap.pretty_output(indent_level+1) + "\n"
        return out_string

    def addVrf(self, vrf):
        ''' Adds a VRF object to the dict of attached VRF's '''
        self.vrfs[vrf.getDn()] = vrf

    def getVrfs(self):
        ''' Returns a dict of VRF Objects '''
        return self.vrfs

    def getTenant(self):
        return self.name

    def addAppProfile(self, ap):
        ''' Adds an AP object to the dict of attached APs '''
        self.aps[ap.getDn()] = ap

    def getAppProfiles(self):
        ''' Returns a dict of Application Profile Objects '''
        return self.aps

    def addL3Out(self, l3out):
        ''' Adds an L3Out object to the dict of attached L3Outs '''
        self.l3outs[l3out.getDn()] = l3out

    def getL3Outs(self):
        ''' Returns a dict of L3Outs Objects '''
        return self.l3outs

    def uniOutVrf(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['tenant_name'] = self.name
        workdict['tenant_desc'] = self.desc
        workdict['tenant_dn'] = self.dn
        output = []

        if len(self.getVrfs()) == 0:
            return [workdict]
        else:
            for vrf_dn,vrf in self.getVrfs().iteritems():
                output.extend(vrf.uniOut(workdict))
        return output    
        
    def uniOutAp(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['tenant_name'] = self.name
        workdict['tenant_desc'] = self.desc
        workdict['tenant_dn'] = self.dn
        output = []
        if len(self.getAppProfiles()) == 0:
            return [workdict]
        else:
            for ap_dn,ap in self.getAppProfiles().iteritems():
                output.extend(ap.uniOut(workdict))
        return output

    def uniOutL3Out(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['tenant_name'] = self.name
        workdict['tenant_desc'] = self.desc
        output = []
        if len(self.getL3Outs()) == 0:
            return [workdict]
        else:
            for l3out_dn,l3out in self.getL3Outs().iteritems():
                output.extend(l3out.uniOut(workdict))
        return output

    def uniOutL3OutRtCtrl(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['tenant_name'] = self.name
        workdict['tenant_desc'] = self.desc
        output = []
        if len(self.getL3Outs()) == 0:
            return [workdict]
        else:
            for l3out_dn,l3out in self.getL3Outs().iteritems():
                output.extend(l3out.uniOutRtCtrl(workdict))
        return output
# end of class MyTenant

class MyVrf(MyAciObjects):
    '''
    A class representing a VRF
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.scope = inputs['scope']
        self.pcTag = inputs['pcTag']
        self.bds = {}
        self.l3outs = {}

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'VRF'

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("VRF Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "BDs:" + "\n"
        for bd in self.bds:
            out_string += bd.pretty_output(indent_level+1) + "\n"
            
        return out_string

    def addBd(self, bd):
        ''' Adds a BD object to the dict of attached BD's '''
        self.bds[bd.getDn()] = bd

    def getBds(self):
        ''' Returns a dict of BD Objects '''
        return self.bds

    def getBdList(self):
        ''' Returns a list of names of attached BDs. '''
        ### bd_list = []
        ### for bd in self.bds:
        ###     bd_list.append(bd.getName())
        ### return bd_list.sort()
        return self.bds.keys()

    def getBdDict(self):
        ''' Returns a dict of names of attached BDs. Key is an integer index. Optimized for function pick_value '''
        bd_dict = {}
        bd_index = 0
        for bd_key in self.bds:
            bd_index += 1
            bd_dict[str(bd_index)] = bd_key
        return bd_dict

    def addL3Out(self, l3out):
        ''' Adds a L3Out object to the dict of attached L3Outs '''
        self.l3outs[l3out.getDn()] = l3out

    def getL3Outs(self):
        ''' Returns a dict of L3Out Objects '''
        return self.l3outs

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['vrf_name'] = self.name
        workdict['vrf_desc'] = self.desc
        workdict['vrf_dn'] = self.dn
        workdict['vrf_scope'] = self.scope
        workdict['vrf_pcTag'] = self.pcTag
        output = []
        #return workdict
        if len(self.getBds()) == 0:
            return [workdict]
        else:
            for bd_key in self.getBds():
                output.extend(self.getBds()[bd_key].uniOut(workdict))
            return output
# end of class MyVrf

class MyBd(MyAciObjects):
    '''
    A class representing a BD, Bridge Domain
    '''
    # Attributes ##################
    # bds = [], is there something attached to a bridge domain?
    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.bcastP = inputs['bcastP']
        self.unkMcastAct = inputs['unkMcastAct']
        self.unkMacUcastAct = inputs['unkMacUcastAct']
        self.arpFlood = inputs['arpFlood']
        self.scope = inputs['scope']
        self.type = inputs['type']
        self.unicastRoute = inputs['unicastRoute']
        self.multiDstPktAct = inputs['multiDstPktAct']
        self.limitIpLearnToSubnets = inputs['limitIpLearnToSubnets']
        self.subnets = {}
        self.vrfDn = ''

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'BD'

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("BD Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "{:_<15}: {}\n".format("Distinguished Name", self.dn)
        out_string += indent + "{:_<15}: {}\n".format("Broadcast IP", self.bcastP)
        out_string += indent + "{:_<15}: {}\n".format("ARP Flooding", self.arpFlood)
        out_string += indent + "{:_<15}: {}\n".format("unkMacUcastAct", self.unkMacUcastAct)
        out_string += indent + "{:_<15}: {}\n".format("IP Learning Subnet", self.limitIpLearnToSubnets)
        out_string += indent + "{:_<15}: {}\n".format("unkMcastAct", self.unkMcastAct)
        out_string += indent + "{:_<15}: {}\n".format("unkMcastAct", self.multiDstPktAct)
        out_string += indent + "Subnets:" + "\n"
        for subnet in self.subnets:
            out_string += subnet.pretty_output(indent_level+1) + "\n"
        return out_string

    def setVrf(self, vrf):
        ''' Sets the Object's VRF to vrf '''
        self.vrfdn = vrf

    def setVrfFromJson(self, inputs):
        ''' Sets the Object's VRF based on JSON input as provided by ACI '''
        self.vrfDn = inputs['tDn']

    def getVrf(self):
        ''' Returns the Object's VRF as a string '''
        return str(self.vrfDn)

    def addSubnet(self, subnet):
        ''' Adds a Subnet object to the dict of attached Subnets '''
        # self.subnets.append(subnet)
        self.subnets[subnet.getDn()] = subnet

    def getSubnets(self):
        ''' Returns a dict of attached Subnets objects '''
        return self.subnets

    def getSubnetIps(self):
        ''' Returns a string, semicolon separated list of subnet addresses '''
        ips = []
        if len(self.subnets) == 0:
            return "n/a"
        else:
            for subnet_key in self.subnets:
                ips.append(self.subnets[subnet_key].getIp())
            return ";".join(ips)

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['bd_name'] = self.name
        workdict['bd_desc'] = self.desc
        workdict['bd_dn'] = self.dn
        workdict['bd_bcastP'] = self.bcastP
        workdict['bd_arpFlood'] = self.arpFlood
        workdict['bd_unkMacUcastAct'] = self.unkMacUcastAct
        workdict['bd_limitIpLearnToSubnets'] = self.limitIpLearnToSubnets
        workdict['bd_unkMcastAct'] = self.unkMcastAct
        workdict['bd_unicastRoute'] = self.unicastRoute
        workdict['bd_multiDstPktAct'] = self.multiDstPktAct
        workdict['bd_subnets'] = self.getSubnetIps()
        return [workdict]
# end of class MyBd

class MySubnet(MyAciObjects):
    '''
    A class representing a Subnet, fvSubnet
    '''
    # Attributes ##################
    #
    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.ip = inputs['ip']
        self.dn = inputs['dn']
        self.preferred = inputs['preferred']
        self.scope = inputs['scope']
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'Subnet'

    def setDn(self, input):
        ''' Sets the object's DN to input '''
        self.dn = input

    def getDn(self):
        ''' Returns the Object's DN as a string '''
        return str(self.dn)

    def getBd(self):
        ''' Returns the Object's BD as a string, derived from DN '''
        bd_elements = self.dn.split("/")
        bd = bd_elements[0] + "/" + bd_elements[1] + "/" + bd_elements[2] 
        return bd

    def setName(self, input):
        ''' Sets the object's name to input '''
        self.name = input

    def getName(self):
        ''' Returns the Object's name as a string '''
        return str(self.name)

    def setDesc(self, input):
        ''' Sets the object's desc to input '''
        self.desc = input

    def getDesc(self):
        ''' Returns the Object's desc as a string '''
        return str(self.desc)

    def setIp(self, input):
        ''' Sets the object's IP to input '''
        self.ip = input

    def getIp(self):
        ''' Returns the Object's IP address as a string '''
        return str(self.ip)

    def setRn(self, input):
        ''' Sets the object's RN to input '''
        self.rn = input

    def getRn(self):
        ''' Returns the Object's RN as a string '''
        return str(self.rn)

    def setPreferred(self, input):
        ''' Sets the object's preferred to input '''
        self.preferred = input

    def getPreferred(self):
        ''' Returns the Object's Preferred as a string '''
        return str(self.preferred)

    def setScope(self, input):
        ''' Sets the object's scope to input '''
        self.scope = input

    def getScope(self):
        ''' Returns the Object's Scope as a string '''
        return str(self.scope)

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("Subnet Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "{:_<15}: {}\n".format("IP", self.ip)
        out_string += indent + "{:_<15}: {}\n".format("RN", self.rn)
        out_string += indent + "{:_<15}: {}\n".format("Preferred", self.preferred)
        out_string += indent + "{:_<15}: {}\n".format("Scope", self.scope)
        return out_string

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['bd_sb_name'] = self.name
        workdict['bd_sb_desc'] = self.desc
        workdict['bd_sb_ip'] = self.ip
        workdict['bd_sb_rn'] = self.rn
        workdict['bd_sb_preferred'] = self.preferred
        workdict['bd_sb_scope'] = self.scope
        output = []
        return [workdict]
# end of class MySubnet

class MyAppProfile(MyAciObjects):
    '''
    A class representing a Application Profile
    '''
    # Class Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.epgs = {}

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'AppProfile'

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("AppProfile Name", self.name)
        out_string += indent + "{:_<15}: {}\n".format("Description", self.desc)
        out_string += indent + "EPGs:" + "\n"
        for epg in self.epgs:
            out_string += epg.pretty_output(indent_level+1) + "\n"
        return out_string

    def addEpg(self, epg):
        ''' Adds a EPG object to the dict of attached EPG's '''
        # self.epgs.append(epg)
        self.epgs[epg.getDn()] = epg

    def getEpgs(self):
        ''' Returns a dict of EPG Objects '''
        return self.epgs

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['ap_name'] = self.name
        workdict['ap_desc'] = self.desc
        workdict['ap_dn'] = self.dn
        output = []
        #return workdict
        if len(self.getEpgs()) == 0:
            return [workdict]
        else:
            for key, value in self.getEpgs().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyAppProfile

class MyEpg(MyAciObjects):
    '''
    A class representing an EPG, Endpoint Group
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.pcEnfPref = inputs['pcEnfPref']
        self.bdDn = ''
        self.scope = inputs['scope']
        self.pcTag = inputs['pcTag']
        self.static_ports = {}
        self.subnets = {}
        self.provContracts = {}
        self.consContracts = {}
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'EPG'

    def setBdDn(self, bddn):
        ''' Sets the EPG bddn to bdnd '''
        self.bddn = bddn

    def getBdDn(self):
        ''' Returns the EPG bddn as a string '''
        return str(self.bddn)

    def setBdDnFromJson(self, inputs):
        ''' Sets the Object's BD DN based on JSON input as provided by ACI '''
        self.bdDn = inputs['tDn']

    def getBd(self):
        ''' Returns the EPG BD as a string, that is the last part of the BD DN '''
        m = re.search('^.*/BD-(.*)$', self.bddn)
        if m:
            bd = m.group(1)
            return str(bd)
        else:
            return str('Error in epg.getBd()')

    def getApDn(self):
        ''' Returns the AP DN based on the DN '''
        m = re.search('^(.*)\/.*$', self.dn)
        apdn = 'Error getting AP DN from DN'
        if m:
            apdn = m.group(1)
        return apdn

    def addSubnet(self, subnet):
        ''' Adds a Subnet object to the dict of attached Subnets '''
        # print "Tenant: ["+self.getTenant()+"], EPG: ["+self.getName()+"], added Subnet ["+subnet.getIp()+"]"
        self.subnets[self.dn+"/"+subnet.getRn()] = subnet

    def getSubnets(self):
        ''' Returns a dict of attached Subnets objects '''
        return self.subnets

    def addProvContract(self, contract):
        ''' Adds a MyProvContract object to the dict of attached provContracts '''
        self.provContracts[contract.getDn()] = contract

    def getProvContracts(self):
        ''' Returns a dict of attached provContracts objects '''
        return self.provContracts

    def addConsContract(self, contract):
        ''' Adds a MyProvContract object to the dict of attached provContracts '''
        self.consContracts[contract.getDn()] = contract

    def getConsContracts(self):
        ''' Returns a dict of attached provContracts objects '''
        return self.consContracts

    def getSubnetIps(self):
        ''' Returns a string, semicolon separated list of subnet addresses '''
        ips = []
        if len(self.subnets) == 0:
            return "n/a"
        else:
            for subnet_key in self.subnets:
                ips.append(self.subnets[subnet_key].getIp())
            return ";".join(ips)

    def getProvContractNames(self):
        ''' Returns a string, semicolon separated list of attached provider contracts '''
        provContracts = []
        if len(self.provContracts) == 0:
            return "n/a"
        else:
            for contract_key, contract in self.provContracts.iteritems():
                provContracts.append(contract.getTdn())
            return ";".join(provContracts)

    def getConsContractNames(self):
        ''' Returns a string, semicolon separated list of attached consumer contracts '''
        consContracts = []
        if len(self.consContracts) == 0:
            return "n/a"
        else:
            for contract_key, contract in self.consContracts.iteritems():
                consContracts.append(contract.getTdn())
            return ";".join(consContracts)

    def addStaticPort(self, static_port):
        ''' Adds a MyStaticPort object to the dict of attached static ports '''
        self.static_ports[static_port.getDn()] = static_port

    def getStaticPorts(self):
        ''' Returns a dict of MyStaticPort Objects '''
        return self.static_ports

    def getStaticPortsSet(self):
        ''' Returns a set of topology info of the attached ports '''
        ports = []
        for port_key in self.static_ports:
            ports.extend([self.static_ports[port_key].getTdn()])
        return set(ports)

    def getConsContractsSet(self):
        ''' Returns a set of consumed contracts '''
        contracts = []
        for cont_key, cont in self.consContracts.iteritems():
            contracts.append(cont.getTdn())
        return set(contracts)

    def getProvContractsSet(self):
        ''' Returns a set of consumed contracts '''
        contracts = []
        for cont_key, cont in self.provContracts.iteritems():
            contracts.append(cont.getTdn())
        return set(contracts)

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['epg_name'] = self.name
        workdict['epg_desc'] = self.desc
        workdict['epg_dn'] = self.dn
        workdict['epg_pcEnfPref'] = self.pcEnfPref
        workdict['epg_scope'] = self.scope
        workdict['epg_pcTag'] = self.pcTag
        workdict['epg_bdDn'] = self.bdDn
        workdict['epg_subnets'] = self.getSubnetIps()
        workdict['epg_prov_contracts'] = self.getProvContractNames()
        workdict['epg_cons_contracts'] = self.getConsContractNames()
        output = []
        #return workdict
        if len(self.getStaticPorts()) == 0:
            return [workdict]
        else:
            for key, value in self.getStaticPorts().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyEpg

class MyStaticPort(MyAciObjects):
    '''
    A class representing a static port in an EPG
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.dn = inputs['dn']
        self.tdn = inputs['tDn']
        self.encap = inputs['encap']
        self.primaryEncap = inputs['primaryEncap']
        self.mode = inputs['mode']

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyStaticPort'

    def setDn(self, dn):
        ''' Sets the Object's DN to dn '''
        self.dn = dn

    def getDn(self):
        ''' Returns the Object's DN as a string '''
        return str(self.dn)

    def setTdn(self, tdn):
        ''' Sets the Object's TDN to tdn '''
        self.tdn = tdn

    def getTdn(self):
        ''' Returns the Object's TDN as a string '''
        return str(self.tdn)

    def getEpg(self):
        ''' Returns the Object's EPG as a string, derived from DN '''
        epg_elements = self.dn.split("/")
        epg = epg_elements[0] + "/" + epg_elements[1] + "/" + epg_elements[2] + "/" + epg_elements[3] 
        return epg

    def pretty_output(self, indent_level = 0, default_indent = '  '):
        indent = indent_level * default_indent
        out_string = indent + "{:_<15}: {}\n".format("tDn", self.tdn)
        out_string += indent + "{:_<15}: {}\n".format("DN", self.dn)
        out_string += indent + "{:_<15}: {}\n".format("Encap", self.encap)
        out_string += indent + "{:_<15}: {}\n".format("Primary Encap", self.primaryEncap)
        out_string += indent + "{:_<15}: {}\n".format("Mode", self.mode)
        return out_string

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['static_port_tdn'] = self.tdn
        workdict['static_port_encap'] = self.encap
        workdict['static_port_primary_encap'] = self.primaryEncap
        workdict['static_port_mode'] = self.mode
        return [workdict]
# end of class MyStaticPort

class MyProvContract(MyAciObjects):
    '''
    A class representing a provider contract attached to an EPG
    '''
    # Attributes ##################
    # Methods #####################
    def __init__(self, inputs):
        # self.epgDn = inputs['tDn']
        self.dn = inputs['dn']
        self.tDn = inputs['tDn']
        self.tnVzBrCPName = inputs['tnVzBrCPName']
        self.type = "provider"

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyProvContract'

    def setDn(self, dn):
        ''' Sets the Object's DN to dn '''
        self.dn = dn

    def getDn(self):
        ''' Returns the Object's TDN as a string. Treat this as a pseudo DN '''
        return str(self.dn)

    def getEpgDn(self):
        ''' Returns the EPG DN based on the Object's DN as a string. Treat this as a pseudo DN '''
        m = re.search('^(.*)\/.*$', self.dn)
        epgdn = 'Error getting epgdn DN from DN'
        if m:
            epgdn = m.group(1)
        return epgdn

    def setTdn(self, tdn):
        ''' Sets the Object's TDN to tdn '''
        self.tDn = tdn

    def getTdn(self):
        ''' Returns the Object's TDN as a string '''
        return str(self.tDn)

    def setType(self, type):
        ''' Sets the Object's type to type '''
        self.type = type

    def getType(self):
        ''' Returns the Object's type as a string '''
        return str(self.type)

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['prov_contract_dn'] = self.dn
        workdict['prov_contract_tdn'] = self.tDn
        workdict['prov_contract_type'] = self.type
        workdict['prov_contract_tnVzBrCPName'] = self.tnVzBrCPName
        return [workdict]

# end of class MyProvContract

class MyConsContract(MyAciObjects):
    '''
    A class representing a consumer contract attached to an EPG
    '''
    # Attributes ##################
    # Methods #####################
    def __init__(self, inputs):
        # self.epgDn = inputs['tDn']
        self.dn = inputs['dn']
        self.tDn = inputs['tDn']
        self.tnVzBrCPName = inputs['tnVzBrCPName']
        self.type = "consumer"

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyProvContract'

    def setDn(self, dn):
        ''' Sets the Object's DN to dn '''
        self.dn = dn

    def getDn(self):
        ''' Returns the Object's DN as a string. Treat this as a pseudo DN '''
        return str(self.dn)

    def getEpgDn(self):
        ''' Returns the EPG DN based on the Object's DN as a string. Treat this as a pseudo DN '''
        m = re.search('^(.*)\/.*$', self.dn)
        epgdn = 'Error getting epgdn DN from DN'
        if m:
            epgdn = m.group(1)
        return epgdn

    def setTdn(self, tdn):
        ''' Sets the Object's TDN to tdn '''
        self.tDn = tdn

    def getTdn(self):
        ''' Returns the Object's TDN as a string '''
        return str(self.tDn)

    def setType(self, type):
        ''' Sets the Object's type to type '''
        self.type = type

    def getType(self):
        ''' Returns the Object's type as a string '''
        return str(self.type)

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['cons_contract_dn'] = self.dn
        workdict['cons_contract_tdn'] = self.tDn
        workdict['cons_contract_type'] = self.type
        workdict['cons_contract_tnVzBrCPName'] = self.tnVzBrCPName
        return [workdict]

# end of class MyConsContract

class MyL3Out(MyAciObjects):
    '''
    A class representing an L3Out, External routed network
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['name']
        self.desc = inputs['descr']
        self.dn = inputs['dn']
        self.vlan = "n/a"
        self.vxlan = "n/a"
        self.bcastp = "n/a"
        self.domain = "n/a"
        self.vrf = "n/a"
        self.l3extLNodePs = {}
        self.l3extInstPs = {}
        self.l3rtctrlProfiles = {}
        self.dummydicts = {}

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'L3Out'

    def setName(self, name):
        ''' Sets the L3Out name to name '''
        self.name = name

    def getName(self):
        ''' Returns the L3Out name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the L3Out desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the L3Out desc as a string '''
        return str(self.desc)

    def setVrf(self, vrf):
        ''' Sets the L3Out vrf to vrf '''
        self.vrf = vrf

    def getVrf(self):
        ''' Returns the L3Out vrf as a string '''
        return str(self.vrf)

    def setDn(self, dn):
        ''' Sets the L3Out dn to dn '''
        self.dn = dn

    def getDn(self):
        ''' Returns the L3Out dn as a string '''
        return str(self.dn)

    def getVlan(self):
        ''' Returns the L3Out vlan as a string '''
        return str(self.vlan)

    def setVlan(self, vlan):
        ''' Sets the L3Out vlan to vlan '''
        self.vlan = vlan

    def getVxlan(self):
        ''' Returns the L3Out vxlan as a string '''
        return str(self.vxlan)

    def setVxlan(self, vxlan):
        ''' Sets the L3Out vxlan to vxlan '''
        self.vxlan = vxlan

    def getBcastp(self):
        ''' Returns the L3Out bcastp as a string '''
        return str(self.bcastp)

    def setBcastp(self, bcastp):
        ''' Sets the L3Out bcastp to bcastp '''
        self.bcastp = bcastp

    def getVrf(self):
        ''' Returns the L3Out vrf as a string '''
        return str(self.vrf)

    def setVrf(self, vrf):
        ''' Sets the L3Out vrf to vrf '''
        self.vrf = vrf

    def getDomain(self):
        ''' Returns the L3Out domain as a string '''
        return str(self.domain)

    def setDomain(self, domain):
        ''' Sets the L3Out domain to domain '''
        self.domain = domain

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def addL3extLNodeP(self, l3extLNodeP):
        ''' Adds a l3extLNodeP object to the dict of attached l3extLNodePs '''
        self.l3extLNodePs[l3extLNodeP.getRn()] = l3extLNodeP

    def getL3extLNodePs(self):
        ''' Returns a dict of attached l3extLNodePs objects '''
        return self.l3extLNodePs

    def addL3extInstP(self, l3extInstP):
        ''' Adds a l3extInstP object to the dict of attached l3extInstPs '''
        self.l3extInstPs[l3extInstP.getRn()] = l3extInstP

    def getL3extInstPs(self):
        ''' Returns a dict of attached l3extInstPs objects '''
        return self.l3extInstPs

    def addL3rtctrlProfile(self, l3rtctrlProfile):
        ''' Adds a l3rtctrlProfile object to the dict of attached l3rtctrlProfiles '''
        self.l3rtctrlProfiles[l3rtctrlProfile.getRn()] = l3rtctrlProfile

    def getL3rtctrlProfiles(self):
        ''' Returns a dict of attached l3rtctrlProfiles objects '''
        return self.l3rtctrlProfiles

    def getTenantDn(self):
        ''' Returns the Tenant name based on the DN '''
        tenant = 'Error getting tenant name from DN'
        m = re.search('^(.+)\/.*$', self.dn)
        if m:
            tenant = m.group(1)
        return tenant

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['l3o_name'] = self.name
        workdict['l3o_desc'] = self.desc
        workdict['l3o_dn'] = self.dn
        workdict['l3o_vlan'] = self.vlan
        workdict['l3o_vxlan'] = self.vxlan
        workdict['l3o_bcastp'] = self.bcastp
        workdict['l3o_domain'] = self.domain
        workdict['l3o_vrf'] = self.vrf
        output = []
        #return workdict
        if len(self.getL3extLNodePs()) == 0:
            return [workdict]
        else:
            for key, value in self.getL3extLNodePs().iteritems():
                output.extend(value.uniOut(workdict))
            return output

    def uniOutRtCtrl(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['l3o_name'] = self.name
        workdict['l3o_desc'] = self.desc
        workdict['l3o_vrf'] = self.vrf
        output = []
        #return workdict
        if len(self.getL3rtctrlProfiles()) == 0:
            return [workdict]
        else:
            for key, value in self.getL3rtctrlProfiles().iteritems():
                output.extend(value.uniOutRtCtrl(workdict))
            return output
# end of class MyL3Out

class MyL3extLNodeP(MyAciObjects):
    '''
    A class representing an l3extLNodeP, L3Out Logical node profile
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.nodes = {}             # dict of nodes, every entry is a l3extRsNodeL3OutAtt object
        self.dummydicts = {}
        self.lips = {}              # dict of attached logical interface profiles
        
        # add nodes
        for child in inputs['children']:
            for key, value in child.iteritems():
                if key == 'l3extRsNodeL3OutAtt':
                    self.addNode(MyL3extRsNodeL3OutAtt(value['attributes']))
                elif key == 'l3extLIfP':
                    self.addLip(MyL3extLIfP(value))
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'L3extLNodeP'

    def setName(self, name):
        ''' Sets the logical node profile name to name '''
        self.name = name

    def getName(self):
        ''' Returns the logical node profile name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the logical node profile desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the logical node profile desc as a string '''
        return str(self.desc)

    def setRn(self, rn):
        ''' Sets the logical node profile rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the logical node profile rn as a string '''
        return str(self.rn)

    def addNode(self, node):
        ''' Adds a MyL3extRsNodeL3OutAtt object to the dict of attached nodes '''
        self.nodes[node.getTdn()] = node

    def getNodes(self):
        ''' Returns a dict of attached node objects '''
        return self.nodes
        
    def getNodesString(self):
        ''' return a string containing the attached nodes and router ids '''
        output_str = ""
        node_dict = self.getNodes()
        for node_tdn in sorted(node_dict):
            output_str += "Node: [" + node_dict[node_tdn].getTdn() + "], RouterID: [" + node_dict[node_tdn].getRtrId() + "], Loopback: [" + node_dict[node_tdn].getRtrIdLoopBack() + "]; "
        return output_str

    def addLip(self, lip):
        ''' Adds a logical interface profile object to the dict of attached lips '''
        self.lips[lip.getName()] = lip

    def getLips(self):
        ''' Returns a dict of attached lips objects '''
        return self.lips

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['lnp_name'] = self.name
        workdict['lnp_desc'] = self.desc
        workdict['lnp_rn'] = self.rn
        workdict['lnp_nodes'] = self.getNodesString()
        output = []
        #return workdict
        if len(self.getLips()) == 0:
            return [workdict]
        else:
            for key, value in self.getLips().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyL3extLNodeP

class MyL3extRsNodeL3OutAtt(MyAciObjects):
    '''
    A class representing an l3extRsNodeL3OutAtt, L3Out Logical node profile entry
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.tDn = inputs['tDn']
        self.rn = inputs['rn']
        self.rtrId = inputs['rtrId']
        self.rtrIdLoopBack = inputs['rtrIdLoopBack']
        self.dummydicts = {}

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'L3extRsNodeL3OutAtt'

    def setTdn(self, tDn):
        ''' Sets the oject's tDn to tDn '''
        self.tDn = tDn

    def getTdn(self):
        ''' Returns the object's tDn as a string '''
        return str(self.tDn)

    def setRn(self, name):
        ''' Sets the oject's rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the object's rn as a string '''
        return str(self.rn)

    def setRtrId(self, name):
        ''' Sets the oject's rtrId to rtrId '''
        self.rtrId = rtrId

    def getRtrId(self):
        ''' Returns the object's rtrId as a string '''
        return str(self.rtrId)

    def getRtrId(self):
        ''' Returns the object's rtrId as a string '''
        return str(self.rtrId)

    def getRtrIdLoopBack(self):
        ''' Returns the object's rtrIdLoopBack as a string '''
        return str(self.rtrIdLoopBack)

    def setRtrIdLoopBack(self, name):
        ''' Sets the oject's rtrIdLoopBack to rtrIdLoopBack '''
        self.rtrIdLoopBack = rtrIdLoopBack

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

# end of class MyL3extRsNodeL3OutAtt

class MyL3extLIfP(MyAciObjects):
    '''
    A class representing an l3extLIfP, L3Out Logical interface profile entry
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.paths = {}
        self.dummydicts = {}
        # add paths
        for child in inputs['children']:
            for key, value in child.iteritems():
                if key == 'l3extRsPathL3OutAtt':
                    self.addPath(MyL3extRsPathL3OutAtt(value))

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3extLIfP'

    def setName(self, name):
        ''' Sets the oject's name to name '''
        self.name = name

    def getName(self):
        ''' Returns the object's name as a string '''
        return str(self.name)

    def setRn(self, name):
        ''' Sets the oject's rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the object's rn as a string '''
        return str(self.rn)

    def setDesc(self, desc):
        ''' Sets the oject's desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the object's desc as a string '''
        return str(self.desc)

    def addPath(self, path):
        ''' Adds a path, l3extRsPathL3OutAtt, object to the dict of attached paths '''
        self.paths[path.getTdn()] = path

    def getPaths(self):
        ''' Returns a dict of attached paths, l3extRsPathL3OutAtt, objects '''
        return self.paths

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['lip_name'] = self.name
        workdict['lip_desc'] = self.desc
        workdict['lip_rn'] = self.rn
        output = []
        #return workdict
        if len(self.getPaths()) == 0:
            return [workdict]
        else:
            for key, value in self.getPaths().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyL3extLIfP

class MyL3extRsPathL3OutAtt(MyAciObjects):
    '''
    A class representing an l3extRsPathL3OutAtt, L3Out Logical interface profile path
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.tDn = inputs['attributes']['tDn']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.encap = inputs['attributes']['encap']
        self.ifInstT = inputs['attributes']['ifInstT']
        self.mtu = inputs['attributes']['mtu']
        self.mode = inputs['attributes']['mode']
        self.bgp_peer = "n/a"
        self.bgp_allow_self_as = "n/a"
        self.bgp_local_as = "n/a"
        self.bgp_remote_as = "n/a"
        self.dummydicts = {}
        self.l3extMembers = {}

        try:
            for child in inputs['children']:
                for key, value in child.iteritems():
                    if key == 'l3extMember':
                        self.addL3extMember(value['attributes']['side'], value['attributes']['addr'])
                    elif key == 'bgpPeerP':
                        self.bgp_peer = value['attributes']['addr']
                        self.bgp_allow_self_as = value['attributes']['allowedSelfAsCnt']
                        for child2 in value['children']:
                            try:
                                self.bgp_local_as = child2['bgpLocalAsnP']['attributes']['localAsn']
                            except KeyError:
                                pass
                            try:
                                self.bgp_remote_as = child2['bgpAsP']['attributes']['asn']
                            except KeyError:
                                pass
        except KeyError:
            pass

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3extRsPathL3OutAtt'

    def setTdn(self, tdn):
        ''' Sets the oject's tDn to tdn '''
        self.tDn = tdn

    def getTdn(self):
        ''' Returns the object's tDn as a string '''
        return str(self.tDn)

    def setRn(self, name):
        ''' Sets the oject's rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the object's rn as a string '''
        return str(self.rn)

    def setDesc(self, desc):
        ''' Sets the oject's desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the object's desc as a string '''
        return str(self.desc)

    def setEncap(self, encap):
        ''' Sets the oject's encap to encap '''
        self.encap = encap

    def getEncap(self):
        ''' Returns the object's encap as a string '''
        return str(self.encap)

    def setIfInstT(self, ifInstT):
        ''' Sets the oject's ifInstT to ifInstT '''
        self.ifInstT = ifInstT

    def getIfInstT(self):
        ''' Returns the object's ifInstT as a string '''
        return str(self.ifInstT)

    def setMtu(self, mtu):
        ''' Sets the oject's mtu to mtu '''
        self.mtu = mtu

    def getMtu(self):
        ''' Returns the object's mtu as a string '''
        return str(self.mtu)

    def setMode(self, mode):
        ''' Sets the oject's mode to mode '''
        self.mode = mode

    def getMode(self):
        ''' Returns the object's mode as a string '''
        return str(self.mode)

    def addL3extMember(self, side, ip):
        ''' Adds a l3extMember object to the dict of attached l3extMember '''
        self.l3extMembers[side] = ip

    def getL3extMembers(self):
        ''' Returns a dict of attached l3extMembers objects '''
        return self.l3extMembers

    def getMembersString(self):
        ''' return a string containing the attached members '''
        output_str = ""
        members_dict = self.getL3extMembers()
        for member_side in sorted(members_dict):
            output_str += "Side: [" + member_side + "], IP: [" + members_dict[member_side] + "]; "
        return output_str

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['lipp_tDn'] = self.tDn
        workdict['lipp_desc'] = self.desc
        workdict['lipp_rn'] = self.rn
        workdict['lipp_encap'] = self.encap
        workdict['lipp_ifInstT'] = self.ifInstT
        workdict['lipp_mtu'] = self.mtu
        workdict['lipp_mode'] = self.mode
        workdict['lipp_members'] = self.getMembersString()
        workdict['lipp_bgp_peer'] = self.bgp_peer
        workdict['lipp_bgp_allow_self_as'] = self.bgp_allow_self_as
        workdict['lipp_bgp_remote_as'] = self.bgp_remote_as
        workdict['lipp_bgp_local_as'] = self.bgp_local_as
        output = []
        #return workdict
        if len(self.getDummydicts()) == 0:
            return [workdict]
        else:
            for key, value in self.getDummydicts().iteritems():
                output.extend(value.uniOut(workdict))
            return output

# end of class MyL3extRsPathL3OutAtt

class MyL3extInstP(MyAciObjects):
    '''
    A class representing an l3extInstP, L3Out External network
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.dummydicts = {}
        self.subnets = {}

        try:
            for child in inputs['children']:
                try:
                    self.addSubnet(MyL3extSubnet(child['l3extSubnet']['attributes']))
                except KeyError:
                    pass
        except KeyError:
            pass

    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3extInstP'

    def setName(self, name):
        ''' Sets the logical node profile name to name '''
        self.name = name

    def getName(self):
        ''' Returns the logical node profile name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the logical node profile desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the logical node profile desc as a string '''
        return str(self.desc)

    def setRn(self, rn):
        ''' Sets the logical node profile rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the logical node profile rn as a string '''
        return str(self.rn)

    def addSubnet(self, subnet):
        ''' Adds a subnet object to the dict of attached subnets '''
        self.subnets[subnet.getRn()] = subnet

    def getSubnets(self):
        ''' Returns a dict of attached subnets objects '''
        return self.subnets

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['lnp_name'] = self.name
        workdict['lnp_desc'] = self.desc
        workdict['lnp_rn'] = self.rn
        output = []
        #return workdict
        if len(self.getDummydicts()) == 0:
            return [workdict]
        else:
            for key, value in self.getDummydicts().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyL3extInstP

class MyL3extSubnet(MyAciObjects):
    '''
    A class representing an l3extSubnet, L3Out External network subnet
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.ip = inputs['attributes']['ip']
        self.aggregate = inputs['attributes']['aggregate']
        self.scope = inputs['attributes']['scope']
        self.dummydicts = {}
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3extInstP'

    def setName(self, name):
        ''' Sets the external subnet name to name '''
        self.name = name

    def getName(self):
        ''' Returns the external subnet name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the external subnet desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the external subnet desc as a string '''
        return str(self.desc)

    def setRn(self, rn):
        ''' Sets the external subnet rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the external subnet rn as a string '''
        return str(self.rn)

    def setIp(self, ip):
        ''' Sets the external subnet ip to ip '''
        self.ip = ip

    def getIp(self):
        ''' Returns the external subnet ip as a string '''
        return str(self.ip)

    def setAggregate(self, aggregate):
        ''' Sets the external subnet aggregate to aggregate '''
        self.aggregate = aggregate

    def getAggregate(self):
        ''' Returns the external subnet aggregate as a string '''
        return str(self.aggregate)

    def setScope(self, scope):
        ''' Sets the external subnet scope to scope '''
        self.scope = scope

    def getScope(self):
        ''' Returns the external subnet scope as a string '''
        return str(self.scope)

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOut(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['lnp_name'] = self.name
        workdict['lnp_desc'] = self.desc
        workdict['lnp_rn'] = self.rn
        output = []
        #return workdict
        if len(self.getDummydicts()) == 0:
            return [workdict]
        else:
            for key, value in self.getDummydicts().iteritems():
                output.extend(value.uniOut(workdict))
            return output
# end of class MyL3extSubnet

class MyL3rtctrlProfile(MyAciObjects):
    '''
    A class representing an l3rtctrlProfile, L3Out Route control Profile
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.rtctrlCtxPs = {}
        for child in inputs['children']:
            for key, value in child.iteritems():
                if key == 'rtctrlCtxP':
                    self.addRtctrlCtxPs(MyL3RtctrlCtxP(value))
        
        self.dummydicts = {}
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3rtctrlProfile'

    def setName(self, name):
        ''' Sets the external subnet name to name '''
        self.name = name

    def getName(self):
        ''' Returns the external subnet name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the external subnet desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the external subnet desc as a string '''
        return str(self.desc)

    def setRn(self, rn):
        ''' Sets the external subnet rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the external subnet rn as a string '''
        return str(self.rn)

    def addRtctrlCtxPs(self, rtctrlCtxP):
        ''' Adds a rtctrlCtxP object to the dict of attached rtctrlCtxPs '''
        self.rtctrlCtxPs[rtctrlCtxP.getRn()] = rtctrlCtxP

    def getRtctrlCtxPs(self):
        ''' Returns a dict of attached rtctrlCtxPs objects '''
        return self.rtctrlCtxPs

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOutRtCtrl(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['rtctrl_name'] = self.name
        workdict['rtctrl_desc'] = self.desc
        output = []
        #return workdict
        if len(self.getRtctrlCtxPs()) == 0:
            return [workdict]
        else:
            for key, value in self.getRtctrlCtxPs().iteritems():
                output.extend(value.uniOutRtCtrl(workdict))
            return output
# end of class MyL3rtctrlProfile

class MyL3RtctrlCtxP(MyAciObjects):
    '''
    A class representing an l3RtctrlCtxP, L3Out Route control Profile Context
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.name = inputs['attributes']['name']
        self.desc = inputs['attributes']['descr']
        self.rn = inputs['attributes']['rn']
        self.action = inputs['attributes']['action']
        self.rtctrlRsCtxPToSubjPs = {}
        for child in inputs['children']:
            for key, value in child.iteritems():
                if key == 'rtctrlRsCtxPToSubjP':
                    self.addRtctrlRsCtxPToSubjPs(MyL3RtctrlRsCtxPToSubjP(value))
        
        self.dummydicts = {}
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3RtctrlCtxP'

    def setName(self, name):
        ''' Sets the external subnet name to name '''
        self.name = name

    def getName(self):
        ''' Returns the external subnet name as a string '''
        return str(self.name)

    def setDesc(self, desc):
        ''' Sets the external subnet desc to desc '''
        self.desc = desc

    def getDesc(self):
        ''' Returns the external subnet desc as a string '''
        return str(self.desc)

    def setRn(self, rn):
        ''' Sets the external subnet rn to rn '''
        self.rn = rn

    def getRn(self):
        ''' Returns the external subnet rn as a string '''
        return str(self.rn)

    def addRtctrlRsCtxPToSubjPs(self, rtctrlRsCtxPToSubjP):
        ''' Adds a rtctrlRsCtxPToSubjP object to the dict of attached rtctrlRsCtxPToSubjPs '''
        self.rtctrlRsCtxPToSubjPs[rtctrlRsCtxPToSubjP.getTdn()] = rtctrlRsCtxPToSubjP

    def getRtctrlRsCtxPToSubjPs(self):
        ''' Returns a dict of attached rtctrlRsCtxPToSubjPs objects '''
        return self.rtctrlRsCtxPToSubjPs

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOutRtCtrl(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['rtctrl_ctx_name'] = self.name
        workdict['rtctrl_ctx_desc'] = self.desc
        workdict['rtctrl_ctx_action'] = self.action

        output = []
        #return workdict
        if len(self.getRtctrlRsCtxPToSubjPs()) == 0:
            return [workdict]
        else:
            for key, value in self.getRtctrlRsCtxPToSubjPs().iteritems():
                output.extend(value.uniOutRtCtrl(workdict))
            return output
# end of class MyL3rtctrlProfile

class MyL3RtctrlRsCtxPToSubjP(MyAciObjects):
    '''
    A class representing an l3RtctrlRsCtxPToSubjP, L3Out Route control Profile Context
    '''
    # Attributes ##################

    # Methods #####################
    def __init__(self, inputs):
        self.tDn = inputs['attributes']['tDn']
        self.dummydicts = {}
        
    def getType(self):
        ''' Returns the Object's type as a string, should be overwritten in every child class '''
        return 'MyL3RtctrlRsCtxPToSubjP'

    def setTdn(self, tDn):
        ''' Sets the tDn to tDn '''
        self.tDn = tDn

    def getTdn(self):
        ''' Returns the tDn as a string '''
        return str(self.tDn)

    def addDummydicts(self, dummydict):
        ''' Adds a dummydict object to the dict of attached dummydicts '''
        self.dummydicts[dummydict.getDn()] = dummydict

    def getDummydicts(self):
        ''' Returns a dict of attached dummydicts objects '''
        return self.dummydicts

    def uniOutRtCtrl(self, input = {}):
        ''' Create universal output dicts '''
        workdict = copy.deepcopy(input)
        workdict['rtctrl_mr_tdn'] = self.tDn
        output = []
        #return workdict
        if len(self.getDummydicts()) == 0:
            return [workdict]
        else:
            for key, value in self.getDummydicts().iteritems():
                output.extend(value.uniOutRtCtrl(workdict))
            return output
# end of class MyL3RtctrlRsCtxPToSubjP

######################################
# Functions
######################################
#
def getValue(d = {}, k = ''):
    ''' Function to retrieve a value for the key 'k' from the dict 'd'. Return "n/a" if the key does not exists '''
    if k in d:
        return d[k]
    else:
        return 'n/a'
# end of function getValue

def toggle_value(input):
    '''
    Function to toggle boolean input, and integer input of 1 and 0
    '''
    output = input
    return not output
# end off function toggle_value

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def create_excel(excel_file, tenants):
    '''
    Function to create an excel file containing tenant information
    '''
    wb = xlsxwriter.Workbook(excel_file)
    ws1 = wb.add_worksheet('Tenant-VRF-BD')
    ws2 = wb.add_worksheet('Tenant-AP-EPG-Ports')
    ws3 = wb.add_worksheet('Tenant-L3Out-Ports-BGP')
    ws4 = wb.add_worksheet('Tenant-L3Out-Route-Control')
    format1 = wb.add_format({'bg_color': '#FFFFFF', 'border': 7})
    format2 = wb.add_format({'bg_color': '#F0F0F0', 'border': 7})
    cell_formats = [format1, format2]
    row = 0
    col = 0
    format_sel = 0
    loop_format = cell_formats[format_sel]

    # we need to split the VRF-BD tree, AP-EPG-Ports tree adn L3Out tree

    headline1 = ['Tenant Name','Tenant Desc','VRF Name','VRF Desc','VRF Scope','VRF pcTag','BD Name','BD Desc','BD Broadcast IP','BD ARP Flood','BD unkMacUcastAct','BD IP Learning','BD unkMcastAct','BD Unicast Routing','BD multiDstPktAct','BD Subnet IPs']
    headline2 = ['Tenant Name','Tenant Desc','AP Name','AP Desc','EPG Name','EPG Desc','EPG pcTag','EPG Scope','EPG Isolated','EPG Assoc. BD', 'EPG Provider Contracts', 'EPG Consumer Contracts', 'EPG Subnet IPs', 'EPG Static Port', 'EPG Static Port Encap', 'EPG Static Port Primary Encap', 'EPG Static Port Mode']
    headline3 = ['Tenant Name','Tenant Desc','VRF','L3Out Name','L3Out Desc','L3Out VLAN','L3Out VxLAN','L3Out BcastP','L3Out Domain','L3Out VRF','LNP name','LNP desc','LNP RN', 'LNP Nodes', 'LIP name', 'LIP desc', 'LIPP tDn', 'LIPP desc', 'LIPP Encap', 'LIPP ifInstT', 'LIPP MTU', 'LIPP mode', 'LIPP BGP peer', 'LIPP BGP self AS', 'LIPP BGP Remote AS', 'LIPP BGP Local AS', 'LIPP members']
    headline4 = ['Tenant Name','Tenant Desc','VRF','L3Out Name','L3Out Desc','RtCtrl Profile Name','RtCtrl Profile Desc', 'RtCtrl Context Name', 'RtCtrl Context Desc', 'RtCtrl Context Action', 'RtCtrl Match Rule', 'RtCtrl Match Prefixes' ]

    # write headline1
    for hl in headline1:
        ws1.write(row, col, hl)
        col += 1
    
    # loop over uniOutsVrf
    line_index = ''
    line_index_old = ''
    for tenant_dn,tenant in tenants.iteritems():
        uniOutsVrf = tenant.uniOutVrf()
        for uo in uniOutsVrf:
            line_index = '' + getValue(uo, 'tenant_name') + getValue(uo, 'vrf_name') + getValue(uo, 'bd_name')
            if line_index != line_index_old:
                format_sel = toggle_value(format_sel)
                loop_format = cell_formats[format_sel]
                line_index_old = line_index
                
            row += 1
            col = 0
            ws1.write(row, col, getValue(uo, 'tenant_name'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'tenant_desc'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'vrf_name'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'vrf_desc'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'vrf_scope'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'vrf_pcTag'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_name'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_desc'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_bcastP'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_arpFlood'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_unkMacUcastAct'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_limitIpLearnToSubnets'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_unkMcastAct'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_unicastRoute'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_multiDstPktAct'), loop_format)
            col += 1
            ws1.write(row, col, getValue(uo, 'bd_subnets'), loop_format)
            col += 1

    # set column width to 25 and apply auto-filter
    ws1.set_column(0, col, 25)
    ws1.autofilter(0, 0, row, col-1)
    ws1.freeze_panes(1, 1)

    # write headline2
    row = 0
    col = 0
    line_index = ''
    line_index_old = ''
    format_sel = 0
    loop_format = cell_formats[format_sel]
    for hl in headline2:
        ws2.write(row, col, hl)
        col += 1
            
    # loop over uniOutsAp
    for tenant_dn,tenant in tenants.iteritems():
        uniOutsAp = tenant.uniOutAp()
        
        for uo in uniOutsAp:
            line_index = '' + getValue(uo, 'tenant_name') + getValue(uo, 'ap_name') + getValue(uo, 'epg_name')
            if line_index != line_index_old:
                format_sel = toggle_value(format_sel)
                loop_format = cell_formats[format_sel]
                line_index_old = line_index

            row += 1
            col = 0
            ws2.write(row, col, getValue(uo, 'tenant_name'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'tenant_desc'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'ap_name'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'ap_desc'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_name'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_desc'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_pcTag'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_scope'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_pcEnfPref'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_bdDn'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_prov_contracts'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_cons_contracts'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'epg_subnets'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'static_port_tdn'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'static_port_encap'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'static_port_primary_encap'), loop_format)
            col += 1
            ws2.write(row, col, getValue(uo, 'static_port_mode'), loop_format)
            col += 1

    # set column width to 25 and apply auto-filter
    ws2.set_column(0, col, 25)
    ws2.autofilter(0, 0, row, col-1)
    ws2.freeze_panes(1, 1)

# write headline3
    row = 0
    col = 0
    line_index = ''
    line_index_old = ''
    format_sel = 0
    loop_format = cell_formats[format_sel]
    for hl in headline3:
        ws3.write(row, col, hl)
        col += 1
            
    # loop over uniOutsL3Out
    for tenant_dn,tenant in tenants.iteritems():
        uniOutsL3Out = tenant.uniOutL3Out()
        
        for uo in uniOutsL3Out:
            line_index = '' + getValue(uo, 'tenant_name') + getValue(uo, 'l3o_vrf') + getValue(uo, 'l3o_name') + getValue(uo, 'lnp_name') + getValue(uo, 'lip_name')
            if line_index != line_index_old:
                format_sel = toggle_value(format_sel)
                loop_format = cell_formats[format_sel]
                line_index_old = line_index

            row += 1
            col = 0
            ws3.write(row, col, getValue(uo, 'tenant_name'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'tenant_desc'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_vrf'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_name'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_desc'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_vlan'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_vxlan'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_bcastp'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_domain'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'l3o_vrf'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lnp_name'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lnp_desc'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lnp_rn'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lnp_nodes'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lip_name'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lip_desc'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_tDn'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_desc'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_encap'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_ifInstT'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_mtu'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_mode'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_bgp_peer'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_bgp_allow_self_as'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_bgp_remote_as'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_bgp_local_as'), loop_format)
            col += 1
            ws3.write(row, col, getValue(uo, 'lipp_members'), loop_format)
            col += 1

    # set column width to 25 and apply auto-filter
    ws3.set_column(0, col, 25)
    ws3.autofilter(0, 0, row, col-1)
    ws3.freeze_panes(1, 1)

# write headline4
    row = 0
    col = 0
    line_index = ''
    line_index_old = ''
    format_sel = 0
    loop_format = cell_formats[format_sel]
    for hl in headline4:
        ws4.write(row, col, hl)
        col += 1
            
    # loop over uniOutsL3OutRtCtrl
    for tenant_dn,tenant in tenants.iteritems():
        uniOutsL3OutRtCtrl = tenant.uniOutL3OutRtCtrl()
        
        for uo in uniOutsL3OutRtCtrl:
            line_index = '' + getValue(uo, 'tenant_name') + getValue(uo, 'l3o_vrf') + getValue(uo, 'l3o_name') + getValue(uo, 'rtctrl_name') + getValue(uo, 'rtctrl_ctx_name')
            if line_index != line_index_old:
                format_sel = toggle_value(format_sel)
                loop_format = cell_formats[format_sel]
                line_index_old = line_index

            row += 1
            col = 0
            ws4.write(row, col, getValue(uo, 'tenant_name'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'tenant_desc'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'l3o_vrf'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'l3o_name'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'l3o_desc'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_name'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_desc'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_ctx_name'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_ctx_desc'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_ctx_action'), loop_format)
            col += 1
            ws4.write(row, col, getValue(uo, 'rtctrl_mr_tdn'), loop_format)
            col += 1
            try:
                ws4.write(row, col, "; ".join(l3outs_mr[getValue(uo, 'rtctrl_mr_tdn')]), loop_format)
            except KeyError:
                ws4.write(row, col, 'n/a', loop_format)
            col += 1

    # set column width to 25 and apply auto-filter
    ws4.set_column(0, col, 25)
    ws4.autofilter(0, 0, row, col-1)
    ws4.freeze_panes(1, 1)

    wb.close()
# end of function create_excel

######################################
# Variables
######################################
tenants = {}            # dict of tenants
vrfs = {}               # dict of vrfs
bds = {}                # dict of bds
subnets = {}            # dict of subnets
bd_subnets = {}         # dict of subnets
aps = {}                # dict of aps
epgs = {}               # dict of epgs
static_ports = {}       # dict of static_ports
prov_contracts = {}     # dict of provider contracts
cons_contracts = {}     # dict of consumer contracts
l3outs = {}             # dict of l3outs
l3outs_mr = {}          # dict of l3outs match rules
uniOutsVrf = {}         # dict of universal output dicts for VRF tree, containing Tenant, VRF, BD
uniOutsAp = {}          # dict of universal output dicts for AP tree, containg Tenant, AP, EPG, Static Ports
uniOutsL3Out = {}       # dict of universal output dicts for L3Out tree

valid_envs = ['Env1',]
env = ''
script_dir = sys.path[0] + "/"

######################################
# Main program
######################################
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", type=str, choices=valid_envs, required=True, help="Choose the environment")
args = parser.parse_args()
env = args.env

base_dir = script_dir + "../data/output-files/"+env+"/"
tenant_file = base_dir + "tenants-output.json"
vrf_file = base_dir + "vrfs-output.json"
bd_file = base_dir + "bds-output.json"
bd_subnets_file = base_dir + "bd-subnets-output.json"
ap_file = base_dir + "aps-output.json"
epg_file = base_dir + "epgs-output.json"
prov_contracts_file = base_dir + "provider-contracts-output.json"
cons_contracts_file = base_dir + "consumer-contracts-output.json"
static_ports_file = base_dir + "static-ports-output.json"
l3outs_file = base_dir + "l3outs-output.json"
l3outs_mr_file = base_dir + "l3outs-mr-output.json"

excel_file = base_dir + "aci-logical-topology-"+env+".xlsx"
consistency_file = base_dir + "aci-consistency-check-"+env+".txt"
json_file = base_dir + "json-"+env+".json"

# read input files
with open(tenant_file) as tenant_data:
    tenants_raw = json.load(tenant_data)

for item in tenants_raw:
    temp_tenant = MyTenant(item['fvTenant']['attributes'])
    tenants[temp_tenant.getDn()] = temp_tenant

with open(vrf_file) as vrf_data:
    vrfs_raw = json.load(vrf_data)

for item in vrfs_raw:
    temp_vrf = MyVrf(item['fvCtx']['attributes'])
    vrfs[temp_vrf.getDn()] = temp_vrf

with open(bd_file) as bd_data:
    bds_raw = json.load(bd_data)

for item in bds_raw:
    temp_bd = MyBd(item['fvBD']['attributes'])
    for child in item['fvBD']['children']:
        for key, value in child.iteritems():
            if key == 'fvRsCtx':
                temp_bd.setVrfFromJson(value['attributes'])

    bds[temp_bd.getDn()] = temp_bd

with open(bd_subnets_file) as bd_subnets_data:
    bd_subnets_raw = json.load(bd_subnets_data)

for item in bd_subnets_raw:
    temp_subnet = MySubnet(item['fvSubnet']['attributes'])
    bd_subnets[temp_subnet.getDn()] = temp_subnet

with open(ap_file) as ap_data:
    aps_raw = json.load(ap_data)

for item in aps_raw:
    temp_ap = MyAppProfile(item['fvAp']['attributes'])
    aps[temp_ap.getDn()] = temp_ap

with open(epg_file) as epg_data:
    epgs_raw = json.load(epg_data)

for item in epgs_raw:
    temp_epg = MyEpg(item['fvAEPg']['attributes'])
    for child in item['fvAEPg']['children']:
        for key, value in child.iteritems():
            if key == 'fvRsBd':
                temp_epg.setBdDnFromJson(value['attributes'])

    epgs[temp_epg.getDn()] = temp_epg

with open(static_ports_file) as static_ports_data:
    static_ports_raw = json.load(static_ports_data)

for item in static_ports_raw:
    temp_port = MyStaticPort(item['fvRsPathAtt']['attributes'])
    static_ports[temp_port.getDn()] = temp_port
    
with open(prov_contracts_file) as prov_contract_data:
    prov_contracts_raw = json.load(prov_contract_data)
    
for item in prov_contracts_raw:
    temp_prov_contract = MyProvContract(item['fvRsProv']['attributes'])
    prov_contracts[temp_prov_contract.getDn()] = temp_prov_contract

with open(cons_contracts_file) as cons_contract_data:
    cons_contracts_raw = json.load(cons_contract_data)
    
for item in cons_contracts_raw:
    temp_cons_contract = MyProvContract(item['fvRsCons']['attributes'])
    cons_contracts[temp_cons_contract.getDn()] = temp_cons_contract

with open(l3outs_file) as l3outs_data:
    l3outs_raw = json.load(l3outs_data)

for item in l3outs_raw:
    temp_l3out = MyL3Out(item['l3extOut']['attributes'])
    for child in item['l3extOut']['children']:
        for key, value in child.iteritems():
            if key == 'l3extExtEncapAllocator':
                temp_l3out.setVlan(value['attributes']['encap'])
                temp_l3out.setVxlan(value['attributes']['extEncap'])
                temp_l3out.setBcastp(value['attributes']['bcastP'])
            elif key == 'l3extRsL3DomAtt':
                temp_l3out.setDomain(value['attributes']['tDn'])
            elif key == 'l3extRsEctx':
                temp_l3out.setVrf(value['attributes']['tnFvCtxName'])
            elif key == 'l3extLNodeP':
                temp_l3out.addL3extLNodeP(MyL3extLNodeP(value))
            elif key == 'rtctrlProfile':
                temp_l3out.addL3rtctrlProfile(MyL3rtctrlProfile(value))
            elif key == 'l3extInstP':
                temp_l3out.addL3extInstP(MyL3extInstP(value))

    l3outs[temp_l3out.getDn()] = temp_l3out

with open(l3outs_mr_file) as l3outs_mr_data:
    l3outs_mr_raw = json.load(l3outs_mr_data)
    
for item in l3outs_mr_raw:
    l3outs_mr[item['rtctrlSubjP']['attributes']['dn']] = []
    try:
        for child in item['rtctrlSubjP']['children']:
            try:
                l3outs_mr[item['rtctrlSubjP']['attributes']['dn']].append(child['rtctrlMatchRtDest']['attributes']['ip'])
            except KeyError:
                pass
    except KeyError:
        pass

# now we have everything in different lists
# reverse the process, go from little to big and attach everything to it's parent.
# Probably not elegant, but should do it

# attach provider contracts to EPG
for contract_dn, contract in prov_contracts.iteritems():
    for epg_dn,epg in epgs.iteritems():
        if epg.getDn() == contract.getEpgDn():
            epg.addProvContract(contract)

# attach consumer contracts to EPG
for contract_dn, contract in cons_contracts.iteritems():
    for epg_dn,epg in epgs.iteritems():
        if epg.getDn() == contract.getEpgDn():
            epg.addConsContract(contract)

# attach static port to EPG
for static_port_dn,static_port in static_ports.iteritems():
    epgs[static_port.getEpg()].addStaticPort(static_port)

# attach EPG to AP
for ap_dn,ap in aps.iteritems():
    for epg_dn,epg in epgs.iteritems():
        if epg.getApDn() == ap.getDn():
            ap.addEpg(epg)

# attach AP to Tenant
for tenant_dn,tenant in tenants.iteritems():
    for ap_dn,ap in aps.iteritems():
        if ap.getTenantDn() == tenant.getDn():
            tenant.addAppProfile(ap)

# attach bd_subnet to BD
for bd_subnet_dn,bd_subnet in bd_subnets.iteritems():
    bds[bd_subnet.getBd()].addSubnet(bd_subnet)

# attach BD to VRF
for vrf_dn,vrf in vrfs.iteritems():
    for bd_dn,bd in bds.iteritems():
        if bd.getVrf() == vrf.getDn():
            vrf.addBd(bd)

# attach VRF to Tenant
for tenant_dn,tenant in tenants.iteritems():
    for vrf_dn,vrf in vrfs.iteritems():
        if vrf.getTenantDn() == tenant.getDn():
            tenant.addVrf(vrf)

# attach L3Out to Tenant
for tenant_dn,tenant in tenants.iteritems():
    for l3out_dn,l3out in l3outs.iteritems():
        if l3out.getTenantDn() == tenant.getDn():
            tenant.addL3Out(l3out)

# write tenants as JSON to a file
tenants_json = toJSON(tenants)
# print tenants_json
jf = open(json_file, "w")
jf.write(tenants_json)
jf.close()

print "#########################################################################################################################"

print "Create Excel\n"
create_excel(excel_file, tenants)

print "#########################################################################################################################"
# end of main program
