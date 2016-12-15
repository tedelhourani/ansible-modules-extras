#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
DOCUMENTATION = '''
---
module: bigmon_chain
short_description: Create and remove a bigmon inline service chain.
description:
    - Create and remove a bigmon inline service chain.
version_added: "2.3"
options:
  name:
    description:
     - The name of the chain.
    required: true
  state:
    description:
     - Whether the service chain should be present or absent.
    default: present
    choices: ['present', 'absent']
  access_token:
    description:
     - Bigmon access token.

notes:
  - An environment variable can be used, BIGSWITCH_ACCESS_TOKEN.
'''


EXAMPLES = '''
- name: bigmon inline service chain
      bigmon_chain:
        name: MyChain
        controller: '{{ inventory_hostname }}'
        state: present
'''


RETURN = '''
{
    "changed": true,
    "invocation": {
        "module_args": {
            "access_token": null,
            "controller": "192.168.86.221",
            "name": "MyChain",
            "state": "present",
            "validate_certs": false
        },
        "module_name": "bigmon_chain"
    }
}
'''

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.bigswitch_utils import Rest, Response
from ansible.module_utils.pycompat24 import get_exception

def chain(module):
    try:
        access_token = module.params['access_token'] or os.environ['BIGSWITCH_ACCESS_TOKEN']
    except KeyError:
        e = get_exception()
        module.fail_json(msg='Unable to load %s' % e.message )

    name = module.params['name']
    state = module.params['state']
    controller = module.params['controller']

    rest = Rest(module,
                {'content-type': 'application/json', 'Cookie': 'session_cookie='+access_token},
                'https://'+controller+':8443/api/v1/data/controller/applications/bigchain')

    if None in (name, state, controller):
        module.fail_json(msg='parameter `name` is missing')

    response = rest.get('chain?config=true', data={})
    if response.status_code != 200:
        module.fail_json(msg="failed to obtain existing chain config: {}".format(response.json['description']))

    config_present = False
    matching = [chain for chain in response.json if chain['name'] == name]
    if matching:
        config_present = True

    if state in ('present') and config_present:
        module.exit_json(changed=False)

    if state in ('absent') and not config_present:
        module.exit_json(changed=False)
        
    if state in ('present'):
        response = rest.put('chain[name="%s"]' % name, data={'name': name})
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error creating chain '{}': {}".format(name, response.json['description']))

    if state in ('absent'):
        response = rest.delete('chain[name="%s"]' % name, data={})
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error deleting chain '{}': {}".format(name, response.json['description']))

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            controller=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            validate_certs=dict(type='bool', default='False'),
            access_token=dict(aliases=['BIGSWITCH_ACCESS_TOKEN'], no_log=True)
        )
    )

    try:
        chain(module)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
