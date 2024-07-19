import ansible_runner
import json
import os
import re
import time
import argparse
import shutil
from zabbix_utils import ItemValue, Sender

playbook_path = "/root/sysadmin/playbooks/linux_security_compliance.yaml"
inventory_path = "/root/sysadmin/playbooks/hosts"
zabbix_server = "10.17.1.18"
zabbix_port = "10051"
zabbix_def_hostname = 'Kentech updates'

def read_json_output(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def remove_ansi_escape_codes(text):
    ansi_escape = re.compile(r'\x1b\[([0-9;]*)m')
    return ansi_escape.sub('', text)

def generate_playbook(playbook_template, playbook_path, upgrade_param):
    with open(playbook_template, 'r') as template_file:
        content = template_file.read()

    content = content.replace('{{ upgrade_param }}', upgrade_param)

    with open(playbook_path, 'w') as playbook_file:
        playbook_file.write(content)

def main():
    items = []
    zabbix_sender = Sender(server=zabbix_server, port=zabbix_port)

    parser = argparse.ArgumentParser(description='Run Ansible playbook with optional parameters')
    parser.add_argument('--playbook_template', default=playbook_path, help='Path to the playbook')
    parser.add_argument('--inventory', default=inventory_path, help='Path to the inventory file')
    parser.add_argument('--limit', help='Limit the execution to a specific group or host')
    parser.add_argument('--upgrade', default='no', help='Set apt upgrade parameter (yes or no)')
    
    args = parser.parse_args()

    try:
        shutil.rmtree('/tmp/updates/')
    except:
        os.mkdir('/tmp/updates/');

    os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
    
    generate_playbook(args.playbook_template, '/tmp/sec_compliance_playbook.tmp', args.upgrade)

    run_args = {
        'playbook': '/tmp/sec_compliance_playbook.tmp',
        'inventory': args.inventory,
    }

    if args.limit:
        run_args['limit'] = args.limit

    ansible_result = ansible_runner.run(**run_args)

    os.remove('/tmp/sec_compliance_playbook.tmp')

    json_files = [f for f in os.listdir('/tmp/updates/') if f.endswith('.json')]
    
    if json_files:
        for filename in os.listdir('/tmp/updates/'):
            if filename.endswith('.json'):
                filepath = os.path.join('/tmp/updates/', filename)
                with open(filepath, 'r') as file:
                    data = json.load(file)
                    
                hostname = data['hostname']
                if 'agent.hostname' in hostname:
                    match = re.search(r'\[s\|(.*)\]', hostname)
                    hostname = match.group(1)

                items.append(ItemValue(hostname, 'updates.raw', json.dumps([data]).replace("'", '"')))#.replace("[]", "null")))

        print(f"Sending raw JSON from Servers with Zabbix agent")
        #print(f"Debug: {items}")
        response = zabbix_sender.send(items)
        print(f"Response from Zabbix: {response}\n")

    print(f"Sending ansible log")
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
