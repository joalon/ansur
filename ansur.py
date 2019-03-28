from ansible.module_utils.basic import AnsibleModule
from urllib import request
from urllib.error import HTTPError
import os

AUR_BASE_URL = "https://aur.archlinux.org/"
TMP_DIR = ""
USER = ""

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


def aur_package_fetch(module, name):
    package_path = os.path.join(TMP_DIR, name)
    cmd = [GIT_CMD]
    if os.path.exists(package_path):
        os.chdir(package_path)
        cmd.append("pull")
        if not module.check_mode:
            module.run_command(cmd, check_rc=True, cwd=package_path)
    else:
        aur_repo_url = AUR_BASE_URL + "{}.git".format(name)
        cmd.append(["clone", aur_repo_url])
        if not module.check_mode:
            module.run_command(cmd, check_rc=True, cwd=package_path)
    return True


def aur_package_install(module, name):
    return 0


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state   = dict(required=True, default='present', choices=['present', 'absent', 'latest']),
            name    = dict(required=True)
        ),
        supports_check_mode = False
    )

    name = module.params['name']
    state = module.params['state']


    global PACMAN_CMD
    PACMAN_CMD = module.get_bin_path('pacman', True)

    global GIT_CMD
    GIT_CMD = module.get_bin_path('git', True)

    global MAKEPKG_CMD
    MAKEPKG_CMD = module.get_bin_path('makepkg', True)

    if aur_package_exists(module, name):
        if state == 'present' or state == 'latest':
            aur_package_fetch(module, name)
            aur_package_install(module, name)
            module.exit_json(changed=True, something_else=12345)
        
    module.fail_json(msg="something happened!")
        

if __name__ == '__main__':
    main()
