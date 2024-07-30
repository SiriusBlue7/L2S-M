#!/bin/bash

# Get all VXLAN interfaces in the bridge "brtun"
vxlan_interfaces=$(ovs-vsctl list-ports brtun | grep vxlan)

# Save VXLAN interfaces as an array
vxlan_array=($vxlan_interfaces)

# Print the array (for verification purposes)
echo "VXLAN Interfaces in brtun:"
for vxlan in "${vxlan_array[@]}"; {
    ovs-vsctl del-port $vxlan
}
