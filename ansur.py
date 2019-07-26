from ansible.module_utils.basic import AnsibleModule
from urllib import request
from urllib.parse import urlencode, quote_plus
from urllib.error import HTTPError
from json import loads
from pathlib import Path

import os

TMP_DIR = Path('/tmp')

PACMAN_CMD = None
GIT_CMD = None
MAKEPKG_CMD = None

def find_aur_package(module, name, url='https://aur.archlinux.org/rpc.php'):
    search_term = urlencode({'type': 'search', 'arg': name})
    result = request.urlopen("%s?%s" % (url, search_term)).read()
    parsed_result= loads(result)

    if parsed_result['resultcount'] > 0:
        return parsed_result
    return {}

def fetch_aur_package(module, package_dict, repo_url='https://aur.archlinux.org'):
    download_url = repo_url + package_dict['url_path']

    download_path = TMP_PATH / package_dict['name']

    if download_path.is_dir():
        module.run_command([GIT_CMD, 'pull'], cwd=download_path)
    module.run_command([GIT_CMD, 'clone', download_url], cwd=TMP_DIR)


def install_aur_package(module, name):
    package_path = TMP_DIR / name

    if not module.check_mode:
        module.run_command(["makepkg", "--syncdeps"], cwd=str(package_path.absolute()))
        module.run_command(["makepkg", "--install"], cwd=str(package_path.absolute()))
        module.run_command(["makepkg", "--clean"], cwd=str(package_path.absolute()))
    return True

def remove_aur_package(module, name):
    output = module.run_command(["pacman", "-Rs", name])
    module.fail_json(msg=output)
    return 0

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(required=True, choices=['present', 'absent', 'latest']),
            name    = dict(required=True)
        ),
        supports_check_mode = True
    )

    name = module.params['name']
    state = module.params['state']

    global PACMAN_CMD
    PACMAN_CMD = module.get_bin_path('pacman', True)

    global GIT_CMD
    GIT_CMD = module.get_bin_path('git', True)

    global MAKEPKG_CMD
    MAKEPKG_CMD = module.get_bin_path('makepkg', True)

    package = find_aur_package(module, name)

    if not package:
        print('failed')
        module.fail_json(changed=False, msg='Couldn\'t find package ' + name)

    if state == 'present' or state == 'latest':
        fetch_aur_package(module, {'name': name, 'url_path'=package['URLPath']})
        installed = install_aur_package(module, name)
        module.exit_json(changed=True)
    elif state == 'absent':
        remove_aur_package(name)
        module.exit_json(changed=True)

if __name__ == '__main__':
    main()
