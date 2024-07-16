import ansible_runner
import json
import os
import re
import time
from zabbix_utils import ItemValue, Sender

playbook_path = "/root/sysadmin/playbooks/updates.yaml"
inventory_path = "/root/sysadmin/playbooks/hosts"
zabbix_server = "x.x.x.x"
zabbix_port = "10051"
zabbix_def_hostname = 'Updates'

def read_json_output(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def remove_ansi_escape_codes(text):
    ansi_escape = re.compile(r'\x1b\[([0-9;]*)m')
    return ansi_escape.sub('', text)

def main():
    items = []
    noagents = []
    noagents_raw = []
    zabbix_sender = Sender(server=zabbix_server, port=zabbix_port)

    for filename in os.listdir('/tmp/updates/'):
        os.remove('/tmp/updates/' + filename)

    ansible_result = ansible_runner.run(playbook=playbook_path, inventory=inventory_path)

    json_files = [f for f in os.listdir('/tmp/updates/') if f.endswith('.json')]
    
    if json_files:
        for filename in os.listdir('/tmp/updates/'):
            if filename.endswith('.json'):
                filepath = os.path.join('/tmp/updates/', filename)
                with open(filepath, 'r') as file:
                    data = json.load(file)
                    
                if 'hostname' in data:
                    hostname = data['hostname']
                    if 'agent.hostname' in hostname:
                        match = re.search(r'\[s\|(.*)\]', hostname)
                        hostname = match.group(1)
                        items.append(ItemValue(hostname, 'updates.raw', json.dumps([data]).replace("'", '"')))#.replace("[]", "null")))
                    else:
                        noagents.append({"hostname": hostname})
                        noagents_raw.append(data)
                        hostname = zabbix_def_hostname

        noagents = {"data": noagents}

        print(f"Sending hosts without Zabbix agent for the LLD")
        response = zabbix_sender.send_value(zabbix_def_hostname, 'updates.hosts', json.dumps(noagents).replace("'", '"'))
        print(f"Response from Zabbix: {response}")

        print(f"Wait until the LLD runs on Zabbix")         
        time.sleep(20)

        print(f"Sending raw JSON from agentless Servers")
        response = zabbix_sender.send_value(zabbix_def_hostname, 'updates.raw', json.dumps(noagents_raw).replace("'", '"'))
        print(f"Response from Zabbix: {response}")

        print(f"Sending raw JSON from Servers with Zabbix agent")
        response = zabbix_sender.send(items)
        print(f"Response from Zabbix: {response}")

    print(f"Sending ansible results")

    with open(ansible_result.stdout.name, 'r') as stdout_file:
        stdout_content = stdout_file.read()
    with open(ansible_result.stderr.name, 'r') as stderr_file:
        stderr_content = stderr_file.read()
    clean_stdout = remove_ansi_escape_codes(stdout_content)
    clean_stderr = remove_ansi_escape_codes(stderr_content)
    combined_output = f"STDOUT:\n{clean_stdout}\n\nSTDERR:\n{clean_stderr}"

    response = zabbix_sender.send_value(zabbix_def_hostname, 'ansible.result', combined_output)
    print(f"Response from Zabbix: {response}")
    
    print(f"Done!")

if __name__ == "__main__":
    main()
