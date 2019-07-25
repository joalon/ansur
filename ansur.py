from ansible.module_utils.basic import AnsibleModule
from urllib import request
from urllib.error import HTTPError
from pathlib import Path

import os

AUR_BASE_URL = "https://aur.archlinux.org/"
TMP_DIR = Path('/tmp/')

PACMAN_CMD = None
GIT_CMD = None
MAKEPKG_CMD = None

def aur_package_exists(module, name):
    try:
        aur_url = AUR_BASE_URL + "packages/{}".format(name)
        request.urlopen(aur_url).read()
        return True
    except HTTPError:
        return False
    except request.exceptions.Timeout as e:
        module.fail_json(changed=False, msg=str(e))
    except request.exceptions.TooManyRedirects:
        module.fail_json(changed=False, msg=str(e))

def aur_package_fetch(module, name):
    package_path = TMP_DIR / name
    cmd = [GIT_CMD]
    if package_path.is_dir():
        cmd.append("pull")
        if not module.check_mode:
            output = module.run_command(' '.join(str(s) for s in cmd), cwd=str(package_path.absolute()))
            if not output[0]:
                module.fail_json(msg="Already up to date")
            module.fail_json(msg=output)
    else:
        aur_repo_url = AUR_BASE_URL + "{}.git".format(name)
        cmd.append("clone")
        cmd.append(aur_repo_url)
        cmd.append(str(package_path.absolute()))
        if not module.check_mode:
            output = module.run_command(' '.join(str(s) for s in cmd), cwd=str(package_path.absolute()))
            if not output[0]:
                module.fail_json(msg="Success!")
            module.fail_json(msg=output)
    return True

def aur_package_install(module, name):
    package_path = TMP_DIR / name

    if not module.check_mode:
        module.run_command(["makepkg", "--syncdeps"], cwd=str(package_path.absolute()))
        module.run_command(["makepkg", "--install"], cwd=str(package_path.absolute()))
        module.run_command(["makepkg", "--clean"], cwd=str(package_path.absolute()))
    return True

def aur_package_remove(module, name):
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

    if not aur_package_exists(module, name):
        module.fail_json(changed=False, msg='Couldn\'t find package ' + name)

    if state == 'present' or state == 'latest':
        aur_package_fetch(module, name)
        installed = aur_package_install(module, name)
        module.exit_json(changed=True)
    elif state == 'absent':
        aur_package_remove(name)
        module.exit_json(changed=True)

if __name__ == '__main__':
    main()
