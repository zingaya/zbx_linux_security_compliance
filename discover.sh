#!/bin/sh

# Define the subnets
subnets=$1

# List of IPs to exclude
excluded_ips=""

# File to store the reachable hosts
ansible_hosts_file="./discovered-hosts"

# Initialize the Ansible hosts file
echo "[all]" > $ansible_hosts_file

# Function to check if SSH is open
check_ssh() {
  ip=$1
  sh -c "timeout 0.5 echo -n | nc $ip 22 > /dev/null" && echo $ip >> $ansible_hosts_file
}

# Loop through the subnets and IPs
for subnet in $subnets; do
  for i in $(seq 1 254); do
    ip="$subnet.$i"
    # Check if the IP is in the excluded list
    if echo "$excluded_ips" | grep -qw "$ip"; then
      continue
    fi
    check_ssh $ip &
  done
  wait
done

# Wait for all background processes to complete
wait

echo "Ansible hosts file created: $ansible_hosts_file"
