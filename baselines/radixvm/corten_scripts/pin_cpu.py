#!/usr/bin/env python3

import qmp
import sys

def onlinecpu():
    import numa

    o_cpus = []
    for node in range(0,numa.get_max_node()+1):
        for cpu in sorted(numa.node_to_cpus(node)):
            o_cpus.append(cpu)

    return o_cpus


def pin_proc(pid, core):
    import psutil

    try:
        psutil.Process(pid).cpu_affinity([core])
    except ValueError as e:
        print >> sys.stderr, e
        sys.exit(1)


# 1 --> port number
# 2 --> number of vcpus
query = qmp.QMPQuery("localhost:%s" % (sys.argv[1]))
print(query.cmd("query-cpus-fast"))
response = query.cmd("query-cpus-fast")['return']
o_cpus = [x for x in range(int(sys.argv[2]))]

cpu_nums = len(response)

for i in range(int(sys.argv[2])):
    pid = int(response[i]['thread-id'])
    cpu = o_cpus[i]
    print("Pinning process %d to core %d / %d" % (pid, cpu_nums, cpu))
    pin_proc(pid, cpu)