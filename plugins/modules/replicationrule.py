#!/usr/bin/python
# Copyright: (c) 2024, Dell Technologies
# Apache License version 2.0 (see MODULE-LICENSE or http://www.apache.org/licenses/LICENSE-2.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: replicationrule
version_added: '1.2.0'
short_description: Replication rule operations on a PowerStore storage system
description:
- Performs all replication rule operations on a PowerStore Storage System.
- This module supports get details of an existing replication rule, create new
  replication rule for supported parameters, modify replication rule and
  delete a specific replication rule.
extends_documentation_fragment:
  - dellemc.powerstore.powerstore
author:
- P Srinivas Rao (@srinivas-rao5) <ansible.team@dell.com>
options:
  replication_rule_name:
    description:
    - Name of the replication rule.
    - Required during creation of a replication rule.
    - Parameter I(replication_rule_name) and I(replication_rule_id) are mutually
      exclusive.
    type: str
  replication_rule_id:
    description:
    - ID of the replication rule.
    - ID for the rule is autogenerated, cannot be passed during creation of
      a replication rule.
    - Parameter I(replication_rule_name) and I(replication_rule_id) are mutually
      exclusive.
    type: str
  new_name:
    description:
    - New name of the replication rule.
    - Used for renaming a replication rule.
    type: str
  rpo:
    description :
    - Recovery point objective (RPO), which is the acceptable amount of data,
      measured in units of time, that may be lost in case of a failure.
    required : false
    choices: [ Five_Minutes, Fifteen_Minutes, Thirty_Minutes, One_Hour,
    Six_Hours, Twelve_Hours, One_Day ]
    type: str
  alert_threshold:
    description:
    - Acceptable delay between the expected and actual replication sync
      intervals. The system generates an alert if the delay between the
      expected and actual sync exceeds this threshold.
    - During creation, if not passed, then by default one RPO in minutes
      will be passed.
    - The range of integers supported are in between 0 and 1440
      (inclusive of both).
    required : false
    type: int
  remote_system:
    description:
    - ID or name of the remote system to which this rule will replicate the
      associated resources.
    required : false
    type: str
  remote_system_address:
    description:
    - The management IPv4 address of the remote system.
    - It is required in case the remote system name passed in I(remote_system)
      parameter is not unique on the PowerStore Array.
    - If ID of the remote system is passed then no need to pass
      I(remote_system_address).
    required : false
    type: str
  state:
    description:
    - The state of the replication rule after the task is performed.
    - For Delete operation only, it should be set to C(absent).
    - For all Create, Modify or Get details operations it should be set to
      C(present).
    required : true
    choices: [ present, absent]
    type: str
notes:
- The I(check_mode) is not supported.
'''

EXAMPLES = r'''

- name: Create new replication rule
  dellemc.powerstore.replicationrule:
    array_ip: "{{array_ip}}"
    validate_certs: "{{validate_certs}}"
    user: "{{user}}"
    password: "{{password}}"
    replication_rule_name: "sample_replication_rule"
    rpo: "Five_Minutes"
    alert_threshold: "15"
    remote_system: "WN-D8877"
    state: "present"

- name: Modify existing replication rule
  dellemc.powerstore.replicationrule:
    array_ip: "{{array_ip}}"
    validate_certs: "{{validate_certs}}"
    user: "{{user}}"
    password: "{{password}}"
    replication_rule_name: "sample_replication_rule"
    new_name: "new_sample_replication_rule"
    rpo: "One_Hour"
    alert_threshold: "60"
    remote_system: "WN-D0517"
    state: "present"

- name: Get details of replication rule
  dellemc.powerstore.replicationrule:
    array_ip: "{{array_ip}}"
    validate_certs: "{{validate_certs}}"
    user: "{{user}}"
    password: "{{password}}"
    replication_rule_id: "{{id}}"
    state: "present"

- name: Delete an existing replication rule
  dellemc.powerstore.replicationrule:
    array_ip: "{{array_ip}}"
    validate_certs: "{{validate_certs}}"
    user: "{{user}}"
    password: "{{password}}"
    replication_rule_name: "new_sample_replication_rule"
    state: "absent"
'''

RETURN = r'''

changed:
    description: Whether or not the resource has changed.
    returned: always
    type: bool
    sample: "false"

replication_rule_details:
    description: Details of the replication rule.
    returned: When replication rule exists
    type: complex
    contains:
        id:
            description: The system generated ID of the replication rule.
            type: str
        name:
            description: Name of the replication rule.
            type: str
        alert_threshold:
            description: Acceptable delay in minutes between the expected and
                         actual replication sync intervals.
            type: int
        rpo:
            description: Recovery point objective (RPO), which is the
                         acceptable amount of data, measured in units of time,
                         that may be lost in case of a failure.
            type: str
        remote_system_id:
            description: Unique identifier of the remote system to which this
                         rule will replicate the associated resources.
            type: str
        remote_system_name:
            description: Name of the remote system to which this rule will
                         replicate the associated resources.
            type: str
    sample: {
        "alert_threshold": 15,
        "id": "0a9dc368-3085-4f4b-b7a4-23ec0166542f",
        "is_replica": false,
        "name": "sample_replication_rule",
        "policies": [],
        "remote_system_id": "677f64ff-955a-49ce-9a06-7d5af0ec4929",
        "remote_system_name": "RT-D0101",
        "rpo": "Thirty_Minutes"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.dellemc.powerstore.plugins.module_utils.storage.dell\
    import utils

LOG = utils.get_logger('replicationrule')

py4ps_sdk = utils.has_pyu4ps_sdk()
HAS_PY4PS = py4ps_sdk['HAS_Py4PS']
IMPORT_ERROR = py4ps_sdk['Error_message']

py4ps_version = utils.py4ps_version_check()
IS_SUPPORTED_PY4PS_VERSION = py4ps_version['supported_version']
VERSION_ERROR = py4ps_version['unsupported_version_message']


class PowerstoreReplicationRule(object):
    """Replication Rule operations"""
    cluster_name = ' '
    cluster_global_id = ' '

    def __init__(self):
        """Define all the parameters required by this module"""
        self.module_params = utils.get_powerstore_management_host_parameters()
        self.module_params.update(get_powerstore_replication_rule_parameters())

        # initialize the Ansible module
        mut_ex_args = [['replication_rule_id', 'replication_rule_name']]
        required_one_of = [['replication_rule_id', 'replication_rule_name']]
        self.module = AnsibleModule(
            argument_spec=self.module_params,
            supports_check_mode=False,
            mutually_exclusive=mut_ex_args,
            required_one_of=required_one_of
        )
        LOG.info('HAS_PY4PS = %s , IMPORT_ERROR = %s', HAS_PY4PS,
                 IMPORT_ERROR)
        if HAS_PY4PS is False:
            self.module.fail_json(msg=IMPORT_ERROR)
        LOG.info('IS_SUPPORTED_PY4PS_VERSION = %s , VERSION_ERROR = '
                 '%s', IS_SUPPORTED_PY4PS_VERSION, VERSION_ERROR)
        if IS_SUPPORTED_PY4PS_VERSION is False:
            self.module.fail_json(msg=VERSION_ERROR)

        self.conn = utils.get_powerstore_connection(
            self.module.params)
        self.provisioning = self.conn.provisioning
        LOG.info('Got Py4ps instance for provisioning on PowerStore %s',
                 self.provisioning)
        self.protection = self.conn.protection
        LOG.info('Got Py4ps instance for protection on PowerStore %s',
                 self.protection)

    def get_replication_rule_details(self, rep_rule_name=None,
                                     rep_rule_id=None):
        """Get replication rule details by name or id"""
        try:
            LOG.info('Getting the details of replication rule , Name:%s ,'
                     ' ID:%s', str(rep_rule_name), str(rep_rule_id))
            detail_resp = None
            if rep_rule_name:
                resp = self.protection.get_replication_rule_by_name(
                    rep_rule_name)
                if resp and len(resp) > 0:
                    LOG.info('Successfully got the details of replication rule'
                             'with name: %s on array name: %s and'
                             ' global id: %s', rep_rule_name,
                             self.cluster_name, self.cluster_global_id)
                    detail_resp = self.protection.get_replication_rule_details(
                        resp[0]['id'])
                    return detail_resp
            else:
                detail_resp = self.protection.get_replication_rule_details(
                    rep_rule_id)
                if detail_resp and len(detail_resp) > 0:
                    LOG.info('Successfully got the details of replication '
                             'rule with id: %s from array name: %s and '
                             'global id: %s', id, self.cluster_name,
                             self.cluster_global_id)
                    return detail_resp

            msg = 'No replication rule present with name {0} or ID {1}'.format(
                rep_rule_name, rep_rule_id)
            LOG.info(msg)
            return detail_resp

        except Exception as e:
            msg = 'Get details of replication rule name: {0} or ID {1} on ' \
                  'array name : {2} failed with' \
                  ' error : {3} '.format(rep_rule_name, rep_rule_id,
                                         self.cluster_name, str(e))
            if isinstance(e, utils.PowerStoreException) and \
                    e.err_code == utils.PowerStoreException.HTTP_ERR and \
                    e.status_code == "404":
                LOG.info(msg)
                return None
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def create_replication_rule(self, rep_rule_name=None, rpo=None,
                                remote_system_id=None, alert_threshold=None):
        """ Create replication rule """

        try:
            LOG.info('Creating a replication rule')
            if not rpo:
                msg = "To create a replication rule rpo is required"
                self.module.fail_json(msg=msg)

            resp = self.protection.create_replication_rule(
                name=rep_rule_name, rpo=rpo,
                remote_system_id=remote_system_id,
                alert_threshold=alert_threshold)

            rep_rule_details = self.protection.get_replication_rule_details(
                resp.get('id'))
            LOG.info(
                'Successfully created replication rule, id: %s'
                ' on PowerStore array name : %s , global id : %s',
                resp.get("id"), self.cluster_name,
                self.cluster_global_id)
            return True, rep_rule_details

        except Exception as e:
            msg = 'create replication rule on PowerStore array name' \
                  ': {0} , global id : {1} failed with error ' \
                  '{2}'.format(self.cluster_name, self.cluster_global_id,
                               str(e))
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def modify_replication_rule(self, rep_rule_id, new_name=None,
                                rpo=None, remote_system_id=None,
                                alert_threshold=None):
        """modify an existing replication rule of a given PowerStore storage
        system"""

        try:
            LOG.info('Modifying an existing replication rule')
            resp = self.protection.modify_replication_rule(
                replication_rule_id=rep_rule_id, name=new_name,
                rpo=rpo, remote_system_id=remote_system_id,
                alert_threshold=alert_threshold)

            LOG.info(
                'Successfully modified replication rule id %s of PowerStore'
                ' array name : %s,global id : %s', rep_rule_id,
                self.cluster_name, self.cluster_global_id)
            return True, resp

        except Exception as e:
            msg = 'Modify replication rule id: {0} on PowerStore array ' \
                  'name: {1}, global id:{2} failed with error ' \
                  '{3}'.format(rep_rule_id, self.cluster_name,
                               self.cluster_global_id, str(e))
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def delete_replication_rule(self, rep_rule_id):
        """ Delete a replication rule by id of a given PowerStore storage
         system"""

        try:
            LOG.info('Deleting replication rule id %s', rep_rule_id)
            self.protection.delete_replication_rule(rep_rule_id)

            LOG.info('Successfully deleted replication rule id %s from'
                     ' PowerStore array name : %s , global id : %s',
                     rep_rule_id, self.cluster_name,
                     self.cluster_global_id)
            return True

        except Exception as e:
            msg = 'Delete replication rule id {0} for PowerStore array ' \
                  'name : {1} , global id : {2} failed with error ' \
                  '{3} '.format(rep_rule_id, self.cluster_name,
                                self.cluster_global_id, str(e))
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def get_clusters(self):
        """Get the clusters"""
        try:
            clusters = self.provisioning.get_cluster_list()
            return clusters

        except Exception as e:
            msg = 'Failed to get the clusters with ' \
                  'error {0}'.format(str(e))
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def get_remote_system_details(self, remote_system, remote_system_address):
        """ Get the details of the remote system """
        try:
            LOG.info('Get details of the remote system ')
            remote_system_name = None
            remote_system_id = None
            # Check if ID or name of the remote system is provided
            if remote_system is not None:
                if utils.name_or_id(remote_system) == 'NAME':
                    remote_system_name = remote_system
                else:
                    remote_system_id = remote_system

            if remote_system_name:
                resp = self.protection.get_remote_system_by_name(
                    remote_system_name)
                if resp and len(resp) == 1:
                    return resp[0]
                elif resp and len(resp) > 1:
                    err_msg = 'There are more than one instance with the' \
                              ' same remote system name. Please enter the' \
                              ' remote_system_address to uniquely fetch the' \
                              ' remote system instance.'
                    if not remote_system_address:
                        self.module.fail_json(msg=err_msg)
                    resp = self.protection.get_remote_system_by_name(
                        remote_system_name, remote_system_address)
                    if len(resp) == 1:
                        return resp[0]
                msg = "Remote system with name {0} and address {1} not" \
                      " found. Please enter a valid remote " \
                      "system.".format(remote_system_name,
                                       remote_system_address)
                self.module.fail_json(msg=msg)
            if remote_system_id:
                resp = self.protection.get_remote_system_details(
                    remote_system_id)
                return resp
            return None

        except Exception as e:
            msg = 'Failed to get the remote system with ' \
                  'error {0}'.format(str(e))
            LOG.error(msg)
            self.module.fail_json(msg=msg, **utils.failure_codes(e))

    def perform_module_operation(self):
        """collect input"""
        rep_rule_id = self.module.params['replication_rule_id']
        rep_rule_name = self.module.params['replication_rule_name']
        new_name = self.module.params['new_name']
        rpo = self.module.params['rpo']
        alert_threshold = self.module.params['alert_threshold']
        remote_system = self.module.params['remote_system']
        remote_system_address = self.module.params['remote_system_address']
        state = self.module.params['state']

        result = dict()
        changed = False

        # Get the cluster details
        clusters = self.get_clusters()
        if len(clusters) > 0:
            self.cluster_name = clusters[0]['name']
            self.cluster_global_id = clusters[0]['id']
        else:
            msg = "Unable to find any active cluster on this array"
            LOG.error(msg)
            self.module.fail_json(msg=msg)

        # Fetch remote system id if passed
        remote_system_id = None
        if remote_system:
            remote_system_details = self.get_remote_system_details(
                remote_system, remote_system_address)
            if remote_system_details:
                remote_system_id = remote_system_details['id']

        # Get the details of the replication rule
        rep_rule_details = self.get_replication_rule_details(
            rep_rule_name, rep_rule_id)

        if rep_rule_details and not rep_rule_id:
            rep_rule_id = rep_rule_details['id']
        if rep_rule_details and not rep_rule_name:
            rep_rule_name = rep_rule_details['name']

        # Create a replication rule
        if not rep_rule_details and state == "present":
            if rep_rule_id:
                msg = "To create a replication rule name is required." \
                      " replication_rule_id is passed."
                self.module.fail_json(msg=msg)
            if rep_rule_name is None or rep_rule_name.strip() == '':
                msg = "Invalid rep_rule_name provided. " \
                      "Please enter a valid replication rule name."
                self.module.fail_json(msg=msg)
            if not remote_system:
                msg = "To create a replication rule remote_system is required."
                self.module.fail_json(msg=msg)
            if new_name is not None:
                msg = "new_name parameter passed. Renaming a replication " \
                      "rule is invalid during creation."
                self.module.fail_json(msg=msg)
            changed, rep_rule_details = self.create_replication_rule(
                rep_rule_name, rpo, remote_system_id, alert_threshold)
            rep_rule_id = rep_rule_details['id']

        # Delete a replication rule
        if rep_rule_details and state == "absent":
            changed = self.delete_replication_rule(rep_rule_id)
            rep_rule_details = None

        # Update the details of replication rule
        if rep_rule_details and state == "present":
            # check if rename is required or not.
            name = new_name if new_name is not None\
                else rep_rule_details['name']

            new_rep_rule_dict = {'name': name,
                                 'rpo': rpo,
                                 'remote_system_id': remote_system_id,
                                 'alert_threshold': alert_threshold
                                 }

            to_modify = modify_replication_rule_required(rep_rule_details,
                                                         new_rep_rule_dict)
            LOG.debug("To modify : %s", to_modify)

            if to_modify:
                changed, rep_rule_details = \
                    self.modify_replication_rule(
                        rep_rule_id, new_name, rpo, remote_system_id,
                        alert_threshold)

        if state == "present" and rep_rule_details:
            rep_rule_details = self.show_output(rep_rule_id,
                                                remote_system_address)
        result['changed'] = changed
        result['replication_rule_details'] = rep_rule_details
        self.module.exit_json(**result)

    def show_output(self, rep_rule_id, remote_system_address):
        """
        Return the updated replication rule details.
        """
        LOG.info("Getting details of replication rule to show as output.")

        rep_rule_details = self.get_replication_rule_details(
            rep_rule_id=rep_rule_id)
        rem_sys_id = rep_rule_details['remote_system_id']
        rem_sys_name = self.get_remote_system_details(
            rem_sys_id, remote_system_address)['name']
        rep_rule_details['remote_system_name'] = rem_sys_name
        return rep_rule_details


def modify_replication_rule_required(rep_rule_details, passed_args):
    """ To check if modification is required or not"""
    for key in rep_rule_details.keys():
        if key in passed_args.keys() and\
                passed_args[key] is not None and\
                rep_rule_details[key] != passed_args[key]:
            LOG.debug("Key %s in rep_rule_details=%s,"
                      "passed_args=%s", key,
                      rep_rule_details[key], passed_args[key])
            return True
    return False


def get_powerstore_replication_rule_parameters():
    """This method provide the parameters required for the replication rule
     operations for PowerStore"""

    return dict(
        replication_rule_id=dict(), replication_rule_name=dict(),
        new_name=dict(), alert_threshold=dict(type='int'),
        rpo=dict(required=False, type='str',
                 choices=['Five_Minutes', 'Fifteen_Minutes', 'Thirty_Minutes',
                          'One_Hour', 'Six_Hours', 'Twelve_Hours', 'One_Day']),
        remote_system=dict(), remote_system_address=dict(),
        state=dict(required=True, type='str', choices=['present', 'absent'])
    )


def main():
    """ Create PowerStore replication rule object and perform action on it
        based on user input from playbook """
    obj = PowerstoreReplicationRule()
    obj.perform_module_operation()


if __name__ == '__main__':
    main()
