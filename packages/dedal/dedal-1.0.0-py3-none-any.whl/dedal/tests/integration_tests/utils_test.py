# Dedal library - Wrapper over Spack for building multiple target
# environments: ESD, Virtual Boxes, HPC compatible kernels, etc.

#  (c) Copyright 2025 Dedal developers

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from dedal.utils.utils import set_bashrc_variable


def test_add_new_variable(tmp_path):
    var_name = 'TEST_VAR'
    value = 'test_value'
    bashrc_path = tmp_path / ".bashrc"
    bashrc_path.touch()
    set_bashrc_variable(var_name, value, bashrc_path=str(bashrc_path))
    content = bashrc_path.read_text()
    assert f'export {var_name}={value}' in content


def test_update_existing_variable(tmp_path):
    var_name = 'TEST_VAR'
    value = 'test_value'
    updated_value = 'new_value'
    bashrc_path = tmp_path / ".bashrc"
    bashrc_path.write_text(f'export {var_name}={value}\n')
    set_bashrc_variable(var_name, updated_value, bashrc_path=str(bashrc_path), update_variable=True)
    content = bashrc_path.read_text()
    assert f'export {var_name}={updated_value}' in content
    assert f'export {var_name}={value}' not in content


def test_do_not_update_existing_variable(tmp_path):
    var_name = 'TEST_VAR'
    value = 'test_value'
    new_value = 'new_value'
    bashrc_path = tmp_path / ".bashrc"
    bashrc_path.write_text(f'export {var_name}={value}\n')

    set_bashrc_variable(var_name, new_value, bashrc_path=str(bashrc_path), update_variable=False)

    content = bashrc_path.read_text()
    assert f'export {var_name}={value}' in content
    assert f'export {var_name}={new_value}' not in content


def test_add_variable_with_special_characters(tmp_path):
    var_name = 'TEST_VAR'
    value = 'value_with_$pecial_chars'
    escaped_value = 'value_with_\\$pecial_chars'
    bashrc_path = tmp_path / ".bashrc"
    bashrc_path.touch()

    set_bashrc_variable(var_name, value, bashrc_path=str(bashrc_path))

    content = bashrc_path.read_text()
    assert f'export {var_name}={escaped_value}' in content
