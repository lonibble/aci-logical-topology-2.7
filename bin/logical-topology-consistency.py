#!/usr/bin/python
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
import copy
import time
import ipaddress
import sys
import argparse
import yaml
import json
import pdb
import re

######################################
# Functions
######################################
#
###def getValue(d = {}, k = ''):
###    ''' Function to retrieve a value for the key 'k' from the dict 'd'. Return "n/a" if the key does not exists '''
###    if k in d:
###        return d[k]
###    else:
###        return 'n/a'
#### end of function getValue

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

def compare_dicts(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    # added = d2_keys - d1_keys
    # removed = d1_keys - d2_keys
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    # same = set(o for o in intersect_keys if d1[o] == d2[o])
    return modified
# end of function compare_dicts

def parse_port_tdn(port_tdn):
    """Argument is a string and returns a dict valid for ansible module aci_static_binding_to_epg"""
    #
    # fex='topology/pod-{0}/paths-{1}/extpaths-{2}/pathep-[eth{3}]'.format(pod_id, leafs, extpaths, interface),
    # port_channel='topology/pod-{0}/paths-{1}/pathep-[{2}]'.format(pod_id, leafs, interface),
    # switch_port='topology/pod-{0}/paths-{1}/pathep-[eth{2}]'.format(pod_id, leafs, interface),
    # vpc='topology/pod-{0}/protpaths-{1}/pathep-[{2}]'.format(pod_id, leafs, interface),
    port_infos = {}
    result = re.search('topology\/pod\-([0-9])\/paths\-(.+)\/extpaths\-(.+)\/pathep\-\[eth(.+)\]', port_tdn)
    if result:
        # this is a fex
        port_infos['pod_id'] = result.group(1)
        port_infos['leafs'] = result.group(2)
        port_infos['extpaths'] = result.group(3)
        port_infos['interface'] = result.group(4)
        port_infos['interface_type'] = 'fex'
        return port_infos
        
    result = re.match('topology\/pod\-([0-9])\/paths\-(.+)\/pathep\-\[(.+)\]', port_tdn)
    if result:
        # this is a port_channel
        port_infos['pod_id'] = result.group(1)
        port_infos['leafs'] = result.group(2)
        port_infos['interface'] = result.group(3)
        port_infos['interface_type'] = 'port_channel'
        return port_infos
        
    result = re.match('topology\/pod\-([0-9])\/paths\-(.+)\/pathep\-\[eth(.+)\]', port_tdn)
    if result:
        # this is a switch_port
        port_infos['pod_id'] = result.group(1)
        port_infos['leafs'] = result.group(2)
        port_infos['interface'] = result.group(3)
        port_infos['interface_type'] = 'switch_port'
        return port_infos
        
    result = re.match('topology\/pod\-([0-9])\/protpaths\-(.+)\/pathep\-\[(.+)\]', port_tdn)
    if result:
        # this is a vpc
        port_infos['pod_id'] = result.group(1)
        port_infos['leafs'] = result.group(2)
        port_infos['interface'] = result.group(3)
        port_infos['interface_type'] = 'vpc'
        return port_infos

    else:
      # input is not valid
      print "Input is not valid"
      return None
# end of function parse_port_tdn

def chk_port_groups(aci_lt):
    port_group_result = []
    for tenant_dn,tenant in aci_lt.iteritems():
        for ap_dn,ap in tenant['aps'].iteritems():
            for epg_dn,epg in ap['epgs'].iteritems():
                epg_portset = set()
                epg_vlan_set = set()
                for static_port_dn,static_port in epg['static_ports'].iteritems():
                    epg_portset.add(static_port['tdn'])
                    epg_vlan_set.add(static_port['encap'].replace('vlan-', ''))
                for pg_name, pg_list in consistency_vars['port_groups'].iteritems():
                    diffset = set(pg_list).difference(epg_portset)
                    if (diffset == set(pg_list) ) or (diffset == set()):
                        pass
                    else:
                        port_group_result.append("- tenant:        \"{}\"".format(tenant['name']))
                        port_group_result.append("  ap:            \"{}\"".format(ap['name']))
                        port_group_result.append("  epg:           \"{}\"".format(epg['name']))
                        port_group_result.append("  vlan_id:       \"{}\"".format("; ".join(epg_vlan_set)))
                        port_group_result.append("  port_group:    \"{}\"".format(pg_name))
                        port_group_result.append("  missing_ports:")
                        for missing_port in diffset:
                            port_infos = parse_port_tdn(missing_port)
                            for index, port_key in enumerate(port_infos):
                                if ( index == 0):
                                    port_group_result.append("    - {}: {}".format(port_key, port_infos[port_key]))
                                else:
                                    port_group_result.append("      {}: {}".format(port_key, port_infos[port_key]))

    return port_group_result
# end of function chk_port_groups

def subnet_overlap(aci_lt):
    subnets_consistency = {}
    port_group_result = []
    port_group_result.append("Ignoring tenants starting with: {}".format(consistency_vars['subnet_overlap']['ignore_tenants']))
    skip_tenant = False
    for tenant_dn,tenant in aci_lt.iteritems():
        skip_tenant = False
        try:
            for ignore_tenant in consistency_vars['subnet_overlap']['ignore_tenants']:
                if tenant['name'].startswith(ignore_tenant):
                    skip_tenant = True
        except TypeError:
            pass
        if skip_tenant:
            pass
        else:
            subnets_consistency[tenant['name']] = {}
            for vrf_dn,vrf in tenant['vrfs'].iteritems():
                subnets_consistency[tenant['name']][vrf['name']] = {}
                for bd_dn,bd in vrf['bds'].iteritems():
                    subnets_consistency[tenant['name']][vrf['name']][bd['name']] = []
                    for subnet_dn,subnet in bd['subnets'].iteritems():
                        subnets_consistency[tenant['name']][vrf['name']][bd['name']].append(subnet['ip'])
                        # print "subnet_dn [ {} ], subnet IP [ {} ]".format(subnet_dn,subnet['ip'])
                    if len(subnets_consistency[tenant['name']][vrf['name']][bd['name']]) == 0:
                        del subnets_consistency[tenant['name']][vrf['name']][bd['name']]
                if len(subnets_consistency[tenant['name']][vrf['name']]) == 0:
                    del subnets_consistency[tenant['name']][vrf['name']]
            if len(subnets_consistency[tenant['name']]) == 0:
                del subnets_consistency[tenant['name']]
    
    subnets_consistency_ref = copy.deepcopy(subnets_consistency)
    for tenant_ref in subnets_consistency_ref:
        for vrf_ref in subnets_consistency_ref[tenant_ref]:
            for bd_ref in subnets_consistency_ref[tenant_ref][vrf_ref]:
                for bd_chk in subnets_consistency[tenant_ref][vrf_ref]:
                    if bd_chk == bd_ref:
                        pass
                    else:
                        for subnet_ref in subnets_consistency_ref[tenant_ref][vrf_ref][bd_ref]:
                            for subnet_chk in subnets_consistency[tenant_ref][vrf_ref][bd_chk]:
                                ipnet_ref = ipaddress.ip_interface(unicode(subnet_ref)).network
                                ipnet_chk = ipaddress.ip_interface(unicode(subnet_chk)).network
                                if ipnet_ref.overlaps(ipnet_chk):
                                    port_group_result.append("Tenant["+tenant_ref+"], VRF ["+vrf_ref+"]: ["+bd_ref+"]/["+subnet_ref+"] overlaps with ["+bd_chk+"]/["+subnet_chk+"]")

    return port_group_result
# end of function subnet_overlap

def consumer_contracts(aci_lt):
    consumer_contracts_results = []
    try:
        for cons_cont_key,cons_cont in consistency_vars['consumed_contracts'].iteritems():
            epgs = {}
            try:
                epgs = aci_lt[cons_cont['tenant']]['aps'][cons_cont['ap']]['epgs']
            except KeyError:
                pass
            for epg_key,epg in epgs.iteritems():
                epg_cons_contracts = []
                for epg_cont_key,epg_cont in epg['consContracts'].iteritems():
                    epg_cons_contracts.append(epg_cont['tDn'])
                if cons_cont['contract'] in epg_cons_contracts:
                    pass
                else:
                    consumer_contracts_results.append("["+cons_cont_key+"], EPG ["+epg['dn']+"], Consumed contract ["+cons_cont['contract']+"] MISSING")
    
        return consumer_contracts_results
    except KeyError:
        return consumer_contracts_results
# end of function consumer_contracts

def epg_required_ports(aci_lt):
    epg_required_ports_results = []
    for tenant_dn,tenant in aci_lt.iteritems():
        for ap_dn,ap in tenant['aps'].iteritems():
            for epg_dn,epg in ap['epgs'].iteritems():
                epg_portset = set()
                epg_vlan_set = set()
                for static_port_dn,static_port in epg['static_ports'].iteritems():
                    epg_portset.add(static_port['tdn'])
                try:
                    for req_port_tdn,req_port in consistency_vars['epg_required_ports'].iteritems():
                        if req_port_tdn not in epg_portset:
                            epg_required_ports_results.append("- tenant:   \"{}\"".format(tenant['name']))
                            epg_required_ports_results.append("  ap:       \"{}\"".format(ap['name']))
                            epg_required_ports_results.append("  epg:      \"{}\"".format(epg['name']))
                            epg_required_ports_results.append("  port_tdn: \"{}\"".format(req_port_tdn))
                            epg_required_ports_results.append("  name:     \"{}\"".format(req_port['name']))
                except KeyError:
                    pass
        return epg_required_ports_results
# end of function epg_required_ports

def bd_defaults(aci_lt):
    # Check if some BD settings adhere to the desired default
    bd_defaults_result = []
    bd_defaults_result.append("Ignoring tenants starting with: {}".format(consistency_vars['bd_defaults']['ignore_tenants']))
    skip_tenant = False
    for tenant_dn,tenant in aci_lt.iteritems():
        skip_tenant = False
        for ignore_tenant in consistency_vars['bd_defaults']['ignore_tenants']:
            if tenant['name'].startswith(ignore_tenant):
                skip_tenant = True
        if skip_tenant:
            pass
        else:
            for vrf_dn,vrf in tenant['vrfs'].iteritems():
                for bd_dn,bd in vrf['bds'].iteritems():
                    if len(bd['subnets']) == 0:
                        # this is NOT a routed subnet
                        bd_chk = {k: bd.get(k, None) for k in consistency_vars['bd_defaults']['bd_without_subnet'].keys()}
                        modified = compare_dicts(consistency_vars['bd_defaults']['bd_without_subnet'], bd_chk)
                        if len(modified) > 0:
                            bd_defaults_result.append("- tenant: \"{}\"".format(tenant['name']))
                            bd_defaults_result.append("  bd: \"{}\"".format(bd['name']))
                            bd_defaults_result.append("  difference: \"{}\"".format(modified))
                            bd_defaults_result.append("  subnet: \"{}\"".format('no'))
                    else:
                        # this is a routed subnet
                        bd_chk = {k: bd.get(k, None) for k in consistency_vars['bd_defaults']['bd_with_subnet'].keys()}
                        modified = compare_dicts(consistency_vars['bd_defaults']['bd_with_subnet'], bd_chk)
                        if len(modified) > 0:
                            bd_defaults_result.append("- tenant: \"{}\"".format(tenant['name']))
                            bd_defaults_result.append("  bd: \"{}\"".format(bd['name']))
                            bd_defaults_result.append("  difference: \"{}\"".format(modified))
                            bd_defaults_result.append("  subnet: \"{}\"".format('yes'))

    return bd_defaults_result
# end of function bd_defaults
######################################
# Variables
######################################
script_dir = sys.path[0] + "/"
var_dir = script_dir+"./var-files/"
valid_envs = ['Env1']
env = ''
consistency_vars = {}
tstamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# conditions for logical testing
# Test static ports attached to an EPG
# For Active/Standby cluster it might be necessary that 2 ports are attached to an EPG to ensure failover functionality.
# E.g. firewall cluster nodes are attached to leafs in Pod1 and Pod3, respectively. If there is an EPG where only one port is attached, that might be a problem.

######################################
# Main program
######################################
# define argparse
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", type=str, choices=valid_envs, required=True, help="Choose the environment")
args = parser.parse_args()
env = args.env
# print "Environment: [{}]".format(env)

data_dir = script_dir + "../data/output-files/"+env+"/"
json_file = data_dir + "json-"+env+".json"
var_file = var_dir+"vars-consistency-"+env+".yml"
consistency_file = data_dir + "consistency-check-"+env+".txt"

# import variables for consistency check defined for this environment
consistency_vars = yaml.safe_load(open(var_file))
# print json.dumps(consistency_vars,sort_keys=True,indent=4, separators=(',', ': '))

# import topology info from json file
with open(json_file) as lt_data:
    aci_lt = json.load(lt_data)
# print json.dumps(aci_lt,sort_keys=True,indent=4, separators=(',', ': '))

### Perform consistency checks
###
port_group_result = chk_port_groups(aci_lt)
# print "port_group_result: [ {} ]".format(port_group_result)

subnet_overlap_result = subnet_overlap(aci_lt)
# print "subnet_overlap_result: [ {} ]".format(subnet_overlap_result)

consumer_contracts_result = consumer_contracts(aci_lt)
# print "consumer_contracts_result: [ {} ]".format(consumer_contracts_result)

bd_defaults_result = bd_defaults(aci_lt)
# print "consumer_contracts_result: [ {} ]".format(consumer_contracts_result)

epg_required_ports_results = epg_required_ports(aci_lt)
### 
### End of consistency checks

fh = open(consistency_file,"w")
# Print result
fh.write("{:-<80}\n".format(''))
print "Consistency check for [ {} ] [ {} ]".format(env,tstamp)
fh.write("Consistency check for [ {} ] [ {} ]".format(env,tstamp))
print "{:-<80}".format('')
fh.write("%-80s\n" % (''))
print "{:-<80}".format('Consistency check:  Port groups ')
fh.write("{:-<80}\n".format('Consistency check:  Port groups '))
for line in port_group_result:
    print line
    fh.write(line+"\n")
print "{:-<80}".format('')
fh.write("{:-<80}\n".format(''))
print "{:-<80}".format('Consistency check:  Subnet overlap ')
fh.write("{:-<80}\n".format('Consistency check:  Subnet overlap '))
for line in subnet_overlap_result:
    print line
    fh.write(line+"\n")
print "{:-<80}".format('')
fh.write("{:-<80}\n".format(''))
print "{:-<80}".format('Consistency check:  Consumed contracts ')
fh.write("{:-<80}\n".format('Consistency check:  Consumed contracts '))
for line in consumer_contracts_result:
    print line
    fh.write(line+"\n")
print "{:-<80}".format('')
fh.write("{:-<80}\n".format(''))
print "{:-<80}".format('Consistency check:  BD defaults ')
fh.write("{:-<80}\n".format('Consistency check:  BD defaults '))
for line in bd_defaults_result:
    print line
    fh.write(line+"\n")
print "{:-<80}".format('')
print "{:-<80}".format('Consistency check:  EPG required ports')
fh.write("{:-<80}\n".format('Consistency check:  EPG required ports'))
for line in epg_required_ports_results:
    print line
    fh.write(line+"\n")
print "{:-<80}".format('')
fh.write("{:-<80}\n".format(''))
fh.close()
# end of main program
