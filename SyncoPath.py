import subprocess
import shelve
import os
config_file = shelve.open('configs')


def devices_print(print_style=0):
    """Function to list devices

    :param print_style: 1 if numerated list print else 0
    :return: list of devices
    """
    connect_status = subprocess.check_output("adb devices".split()).decode('utf-8')
    devices = connect_status.strip().split("\n")
    # if daemon is getting started just now
    if '* daemon started successfully *' in devices:
        start_index = 3
    else:
        start_index = 1
    normal = 1 if start_index == 1 else 3
    if len(devices) > normal:
        return_str = [devices[0]]
        if print_style == 0:
            return_str.append('\n'.join(str(e) for e in devices[start_index:]))
        elif print_style == 1:
            for i in enumerate(devices[start_index:]):
                return_str.append(str(i[0]) + "." + i[1])
    else:
        return -1
    return return_str


def auth_check(n, print_=False):
    """Checks if device connected has authorized PC to use adb

    :param n: Index of device in printed list through device_print method
    :param print_: If print_ required along with authentication check
    :return: Tuple with values (status, device_name)
    """
    numerated_device_list = devices_print(1)
    unauthorized_arr = []
    for i in numerated_device_list:
        if print_:
            print(i)
        if 'unauthorized' in i or 'permission' in i:
            unauthorized_arr.append(i)
    # print(n, len(numerated_device_list))
    # print(0 <= n <= len(numerated_device_list)-2)
    if 0 <= n <= len(numerated_device_list)-2:
        pass
    else:
        return -1, ''
    return (0, '') if numerated_device_list[n + 1] in unauthorized_arr else (1,
                                                                             numerated_device_list[n+1].strip('device')
                                                                             )


def list_dir(target_device, parent, device_type='0'):
    """List all files (numerated) in the given directory of given device and returns list

    :param target_device: Name of the device which helps selecting exact device out of multiple connected
    :param parent: Directory which is to be traversed
    :param device_type: Defines type of device to select directory traversing commands accordingly
    :return: List of files/folders in 'parent' directory of 'target_device'
    """

    parent = "/".join(str(e) for e in parent)
    print("Current Directory = %s" % parent)
    if device_type == '0':
        dir_list = list(enumerate(i.strip() for i in subprocess.check_output(['adb',
                                                                              '-s',
                                                                              target_device,
                                                                              'shell',
                                                                              "cd %s; ls -1" % parent]
                                                                             ).decode("utf-8").splitlines()
                                  if i != ''
                                  )
                        )
        # some devices doesn't take flags with ls command
        # if dir_list[0] == (0, "ls"):
        if dir_list[0] == (0, "ls: Unknown option '-1'. Aborting."):
            dir_list = list(enumerate(i.strip() for i in subprocess.check_output(['adb',
                                                                                  '-s',
                                                                                  target_device,
                                                                                  'shell',
                                                                                  "cd %s; ls" % parent]
                                                                                 ).decode("utf-8").splitlines()
                                      if i != ''
                                      )
                            )
    elif device_type == '1':
        dir_list = list(enumerate(os.listdir(parent)))

    for i in range(0, len(dir_list), 4):
        for j in range(4):
            try:
                print('{:{prec}.{prec}}'.format(str(i+j)+". "+dir_list[i+j][1], prec=20), end="\t")
            except IndexError:
                break
        print()
    return dir_list


def sync_function(device, host_dir=".", device_dir="/"):
    """Synchronize files from a device to target

    :param device: Name of the device
    :param host_dir: Path of the directory on computer to be synced with
    :param device_dir: Path of the directory on device to be synced with
    :return: Status message after desired operation
    """
    host_dir = "/".join(str(e) for e in host_dir)
    device_dir = "/".join(str(e) for e in device_dir)
    print("Syncing device's %s with %s of host" % (device_dir, os.path.abspath(host_dir)))
    device_f_set = set(i.strip() for i in subprocess.check_output(["adb",
                                                                   "-s",
                                                                   device,
                                                                   "shell",
                                                                   "cd %s; ls -1" % device_dir]
                                                                  ).decode("utf-8").splitlines()
                       if i != ''
                       )

    # some devices doesn't take flags with ls command
    if list(device_f_set)[0] == "ls: Unknown option '-1'. Aborting.":
        device_f_set = set(i.strip() for i in subprocess.check_output(["adb",
                                                                       "-s",
                                                                       device,
                                                                       "shell",
                                                                       "cd %s; ls" % device_dir]
                                                                      ).decode("utf-8").splitlines()
                           if i != ''
                           )
    host_f_set = set(os.listdir(host_dir))
    host_to_device = list(host_f_set - device_f_set)
    device_to_host = list(device_f_set - host_f_set)

    if len(host_to_device) > len(device_to_host):
        device_to_host += ([''] * (len(host_to_device) - len(device_to_host)))
    else:
        host_to_device += ([''] * (len(device_to_host) - len(host_to_device)))
    print("Transfer...")
    print("{:^{col_width}.{col_width}} \t {:^{prec}.{prec}} \t {:^{prec}.{prec}}".format("Sr. No.", "From Device to PC",
                                                                                         "From PC to Device",
                                                                                         col_width=7, prec=30)
          )

    counter = 0
    for i, j in zip(device_to_host, host_to_device):
        print(
            "{:^{col_width}.{col_width}} \t {:^{prec}.{prec}} \t {:^{prec}.{prec}}".format(str(counter)+".", i, j,
                                                                                           col_width=7,
                                                                                           prec=30)
        )
        counter += 1
    if counter == 0:
        print("{:^67}".format("Voila! Everything seems to be in sync ;)"))
        exit()
    sync_from = input("\n\tPress:\n\t\t1.For Device to PC(Default)\n\t\t2.For PC to Device\n\t\t3.Cancel: ") or '1'
    if sync_from == '3':
        exit()
    sync_what = input("Enter the file indexes separated by comma or 'a'(default) to sync all: ") or 'a'

    if sync_from == '1':
        sync_cmd = ['adb', '-s', device, 'pull', '-p', device_dir+"/@file@", host_dir]
        if sync_what == 'a':
            sync_what = device_to_host
        else:
            sync_what = sync_what.split(',')
            sync_what = [device_to_host[int(i)] for i in sync_what]
    elif sync_from == '2':
        sync_cmd = ['adb', '-s', device, 'push', '-p', device_dir+"/@file@", host_dir]
        if sync_what == 'a':
            sync_what = host_to_device
        else:
            sync_what = sync_what.split(',')
            sync_what = [host_to_device[int(i)] for i in sync_what]
    else:
        exit()
    sync_what = [i for i in sync_what if i != '']
    if sync_what:
        for i in sync_what:
            print("Copying file %s" % i)
            print(subprocess.check_output(sync_cmd[:-2]+[sync_cmd[-2].replace('@file@', i)]+[sync_cmd[-1]]).decode('utf-8'))
        print("\nAll Files have successfully been synced :) ")
    else:
        print("\nNo files to sync from %s to %s" % ('Device', 'PC') if sync_from == '1' else ('PC', 'Device'))


print("Searching and connecting to adb devices...")
devices = devices_print()
if devices == -1:
    print("No device Found")
    more = True
else:
    print("\n".join(str(e) for e in devices))

more_msg = "\nWant to add network devices?(y)es/(n)o/(r)efresh: "

while devices_print() == -1:
    add_more = input(more_msg) or 'n'
    if add_more == 'y' or add_more == 'Y':
        device_address = input("Enter address of the device (i.p.a.dd:port_number): ")
        device_add_status = subprocess.check_output(['adb', 'connect', device_address])
        print(device_add_status.decode('utf-8'))
        more_msg = 'Add more devices?(y)es/(n)o/(r)efresh: '
    elif add_more == 'r' or add_more == 'R':
        subprocess.call('adb kill-server'.split())
        subprocess.check_output('adb start-server'.split())
    elif add_more == 'n' and devices_print() == -1:
        exit()
    else:
        break


auth_check(0, print_=True)
which_device = input("Which device?(0 default): ") or '0'
which_device = int(which_device)

try_again = True
auth_var = auth_check(which_device, print_=False)
while auth_var[0] != 1 or try_again:
    if auth_var[0] == -1:
        print("Please Enter a valid device number.")
        which_device = input("Which device?(0 default): ") or '0'
        which_device = int(which_device)
        try_again = True
    elif auth_var[0] == 0:
        print("\nPlease Allow USB Debugging option in your device first.\n" +
              "(Check on 'Always allow...' if you want to use " +
              "that device again and want it to get authorized automatically.)")
        try_again = input('Try again?(y)es default/(n)o/connect to (d)ifferent device): ') or 'y'
    if try_again == 'y' or try_again == 'Y':
        try_again = True
    elif try_again == 'd' or try_again == 'D':
        which_device = input("Which device?(0 default): ") or '0'
        which_device = int(which_device)
        try_again = True
    else:
        try_again = False
        break
    auth_var = auth_check(which_device, print_=False)

device_name = '.'.join(str(e) for e in auth_var[1].split('.')[1:]).strip()
print("Connected to device %s" % device_name)

directory = []
host_directory = ['.']
where = ''
if device_name in config_file.keys():
    dir_arr = []
    for j in ['device_directory', 'host_directory']:
        try:
            dir_arr.append("/".join(str(e) for e in config_file[device_name][j]))
        except KeyError:
            dir_arr.append('')
    _ = input("Previously synced directory found \"(%s)\" for the device \"%s\" to sync with device \"%s\". Want to"
              " sync it again?(y)es(default)/(n)o: " % (dir_arr[0], os.path.abspath(dir_arr[1]), device_name)) or 'y'
    if _ == 'y':
        directory = config_file[device_name]['device_directory']
        host_directory = config_file[device_name]['host_directory']
        where = 'a'
    else:
        where = 'c'
if not where:
    where = input("Directory: (c)ard(default)/(a)dvanced: ") or 'c'

if where == 'c':
    cards = list(enumerate(subprocess.check_output(['adb', '-s', device_name, 'shell', "ls|grep card"]).decode("utf-8").split()))
    for i in cards:
        print(i[0], '.', i[1])
    which_card = input("Which card?(0 default): ") or '0'
    which_card = int(which_card)
    directory.append(cards[which_card][1])

    print("Choose a directory in PC to sync with...")

    while True:
        print("Host directory", os.path.abspath("/".join(str(e) for e in host_directory)))
        dir_arr = [i[1] for i in list_dir('', parent=host_directory, device_type='1')]
        sub_search = input("\n\tChange directory? directory_index/(u)p /-1 -> done  (default): ") or '-1'
        if sub_search == '-1':
            break
        elif sub_search == 'u' or sub_search == 'U':
            # host_directory = host_directory[:-1]
            host_directory = os.path.abspath(os.path.join("/".join(str(e) for e in host_directory), os.pardir)).split("/")
            continue
        sub_search = dir_arr[int(sub_search)]
        print("\n===")
        print(sub_search)
        print("===")
        host_directory.append(sub_search)

    print("Choose a device directory to sync with...")
    while True:
        dir_arr = [i[1] for i in list_dir(device_name, parent=directory)]
        sub_search = input("\n\tChange directory? directory_index/(u)p /-1 -> done  (default): ") or '-1'
        if sub_search == '-1':
            break
        elif sub_search == 'u' or sub_search == 'U':
            directory = directory[:-1]
            continue
        sub_search = dir_arr[int(sub_search)]
        print("\n===")
        print(sub_search)
        print("===")
        directory.append(sub_search)
    print("saving... ", directory)
    config_file[device_name] = {'host_directory': host_directory, 'device_directory': directory}
    config_file.close()

elif where == 'a':
    if not directory:
        directory = input("Enter the path of the folder you want to sync: eg. sdcard/folder_name") or exit()
    if not host_directory:
        host_directory = input("Enter the path of the folder you want to sync in host: dir/folder") or exit()

sync_function(device_name, host_directory, directory)