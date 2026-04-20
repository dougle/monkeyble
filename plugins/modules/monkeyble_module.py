# Copyright 2022 Hewlett Packard Enterprise Development LP
import unittest.mock

import yaml
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.arg_spec import ValidationResult


class MockedValidationResult(ValidationResult):
    def __init__(self, parameters):
        self._mocked_supported_parameters = dict()
        super().__init__(parameters)

    @property
    def _supported_parameters(self):
        for item, param_list in self._mocked_supported_parameters.items():
            # print(self._mocked_supported_parameters[item])
            self._mocked_supported_parameters[item] = tuple([[x for x in param_list[0] if x != "_mock"], param_list[1]])

        return self._mocked_supported_parameters

    @_supported_parameters.setter
    def _supported_parameters(self, value):
        self._mocked_supported_parameters = value

# a wrapper class to divert calls to the model name
# and pass back the original instead
class MockedAnsibleModule(AnsibleModule):

    # return the original module name
    @property
    def _name(self):
        # module doesn't seem to decode past one level
        mock_params = yaml.safe_load(self.params['_mock'])
        return mock_params['original_module_name']

    # discard any assignments
    @_name.setter
    def _name(self, name):
        pass

def run_module():
    # instantiate ansible module but catch error
    # get params out of the shallow object
    with unittest.mock.patch("ansible.module_utils.basic.AnsibleModule.fail_json", return_value=None):
        fake_module = AnsibleModule(bypass_checks=True, argument_spec={"_mock": dict(type='dict')})
        params = fake_module.params

    # restore original module arg_spec for validation
    module_arg_spec = params['_mock']['original_arg_spec']
    module_arg_spec.update({
        '_mock': {
            'task_name': dict(type='str', required=True),
            'original_module_name': dict(type='str', required=True),
            'consider_changed': dict(type='bool', required=False, default=False),
            'result_dict': dict(type='dict', required=False),
            'original_arg_spec': dict(type='dict')
        }
    })

    # run this module but filter out the _mock module from supported_parameters
    # see mock class above
    with unittest.mock.patch("ansible.module_utils.common.arg_spec.ValidationResult", MockedValidationResult):
        module = MockedAnsibleModule(
            argument_spec=module_arg_spec,
            supports_check_mode=True
        )

    module.log(msg='Monkeyble mock module started')

    # CHANGED
    result = {
        'changed': params['_mock']['consider_changed'],
        'msg': f"Monkeyble Mock module called. Original module: {params['_mock']['original_module_name']}"
    }

    # RESULT DICT
    if params['_mock']['result_dict']:
        result.update(params['_mock']['result_dict'])

    module.exit_json(**result)


def main():
    # local testing
    # set_module_args({
    #     'task_name': 'test',
    #     'original_module_name': "copy"
    #
    # })
    run_module()


if __name__ == '__main__':
    main()
