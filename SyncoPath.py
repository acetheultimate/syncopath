#!/usr/bin/env python3
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
        return '-1'
    return return_str


def auth_check(n, print_=False):
    """Checks if device connected has authorized PC to use adb

    :param n: Index of device in printed list through device_print method
    :param print_: If print_ required along with authentication check
    :return: Tuple with values (status, device_name)
    """
    numerated_device_list = devices_print(1)
    unauthorized_arr = []
    for i in iter(numerated_device_list):
        if print_:
            print(i)
        if 'unauthorized' in i or 'permission' in i:
            unauthorized_arr.append(i)
    if 0 <= n <= len(numerated_device_list) - 2:
        pass
    else:
        return -1, ''
    return (0, '') if numerated_device_list[n + 1] in unauthorized_arr else (1,
                                                                             numerated_device_list[n + 1].strip(
                                                                                 'device')
                                                                             )


def list_dir(target_device, parent, device_type='0', listing_type='a', numerated=True, prints=True):
    """List all files (numerated) in the given directory of given device and returns list

    :param target_device: Name of the device which helps selecting exact device out of multiple connected
    :param parent: Directory which is to be traversed
    :param device_type: Defines type of device to select directory traversing commands accordingly
                        '0' -> Android Device
                        '1' -> PC
    :param listing_type: Whether to list directories or files or everything
                        'a' -> List everything in the directory
                        'f' -> List files only
                        'd' -> List directories only
    :param numerated: Whether list generation is simple or numerated
        :type: numerated bool
    :param prints: Whether to return a list or just print
        :type: prints bool
    :return: List of files/folders in 'parent' directory of 'target_device'
    """

    parent = "/".join(str(e) for e in parent)
    dir_list = []
    if device_type == '0':
        options = ''
        if listing_type == 'f':
            options = 'F'
        elif listing_type == 'd':
            options = 'd */'
        dir_iter = subprocess.check_output(['adb',
                                            '-s',
                                            target_device,
                                            'shell',
                                            "cd %s; ls -1%s" % (parent, options)]
                                           ).decode("utf-8").splitlines()
        # Legacy devices don't take flags with ls command
        if dir_iter[0] == "ls: Unknown option '-1'. Aborting.":
            print("Listing in Legacy Device Mode: ")
            dir_iter = subprocess.check_output(['adb',
                                                '-s',
                                                target_device,
                                                'shell',
                                                "cd %s; ls -F" % parent]
                                               ).decode("utf-8").splitlines()
        dir_iter = (i.strip() for i in dir_iter if i != '')
        if listing_type == 'a':
            dir_list = (i[2:] for i in dir_iter)
        elif listing_type == 'd':
            dir_list = (i[2:] for i in dir_iter if i.startswith("d "))
        elif listing_type == 'f':
            dir_list = (i[2:] for i in dir_iter if not i.startswith("- "))

    elif device_type == '1':
        dir_list = os.listdir(parent)
        if listing_type == 'f':
            dir_list = [i for i in dir_list if os.path.isfile(os.path.abspath(os.path.join(parent, i)))]
        elif listing_type == 'd':
            dir_list = [i for i in dir_list if os.path.isdir(os.path.abspath(os.path.join(parent, i)))]
    # return Type of the list
    if numerated:
        dir_list = list(enumerate(dir_list))
    else:
        dir_list = list(dir_list)
    if prints:
        for i in range(0, len(dir_list), 4):
            for j in range(4):
                try:
                    print('{:{prec}.{prec}}'.format(str(i + j) + ". " + dir_list[i + j][1], prec=20), end="\t")
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
    device_f_set = set(list_dir(target_device=device, parent=device_dir, device_type='0',
                                listing_type='a', numerated=False, prints=False))
    host_dir = "/".join(str(e) for e in host_dir)
    device_dir = "/".join(str(e) for e in device_dir)
    print("Syncing device's %s with %s of host" % (device_dir, os.path.abspath(host_dir)))

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
            "{:^{col_width}.{col_width}} \t {:^{prec}.{prec}} \t {:^{prec}.{prec}}".format(str(counter) + ".", i, j,
                                                                                           col_width=7,
                                                                                           prec=30)
        )
        counter += 1
    if counter == 0:
        print("{:^67}".format("Voila! Everything seems to be in sync ;)"))
        exit()
    sync_from = input("\n\tPress:\n"
                      "\t\t1.For Device to PC(Default)\n"
                      "\t\t2.For PC to Device\n"
                      "\t\t\t***USE WITH CAUTION***\n"
                      "\t\t\tClone from Source to Target\n"
                      "\t\t\t\tif not in Source, delete from Target also\n"
                      "\t\t\t\tif not in Target, copy from Source to target\n"
                      "\t\t3. Clone Device to PC\n"
                      "\t\t4. Clone PC to Device\n"
                      "\t\t5. Cancel: ") or '1'
    if sync_from == '5':
        exit()

    # No need to ask for file index while cloning
    if not (sync_from == '3' or sync_from == '4'):
        sync_what = input("Enter the file indexes separated by comma or 'a'(default) to sync all: ") or 'a'
    else:
        sync_what = 'a'

    # Sync or Clone from Device to PC
    if sync_from == '1' or sync_from == '3':
        sync_cmd = ['adb', '-s', device, 'pull', '-p', device_dir + "/@file@", host_dir]
        # 'a' for all, Clone is 'a' by logic
        if sync_what == 'a' or sync_from == '3':
            sync_what = device_to_host
        else:
            sync_what = sync_what.split(',')
            sync_what = [device_to_host[int(i)] for i in sync_what]
    # Sync or Clone from PC to device
    elif sync_from == '2' or '4':
        sync_cmd = ['adb', '-s', device, 'push', '-p', host_dir + "/@file@", device_dir + "/@file@"]
        if sync_what == 'a' or sync_what == '4':
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
            print(subprocess.check_output(sync_cmd[:-2]
                                          + [sync_cmd[-2].replace('@file@', i)]
                                          + [sync_cmd[-1].replace('@file@', i)]
                                          ).decode('utf-8')
                  )
        print("\nAll Files have successfully been copied :) ")
    else:
        _ = ('Device', 'PC') if sync_from == '1' or '3' else ('PC', 'Device')
        print("\nNo files to Copy from %s to %s" % _)
    # if Cloning , after done copying, Delete from target if not in source
    if sync_from == '3' or sync_from == '4':
        clone_cmd = ''
        clone_tbd_set = ''
        # Cloning from Device to PC
        if sync_from == '3':
            clone_tbd_set = host_f_set - device_f_set
            clone_cmd = ["rm", '"%s/%s"' % (host_dir, "@file@")]

        # Cloning from PC to Device
        elif sync_from == '4':
            clone_tbd_set = device_f_set - host_f_set
            clone_cmd = ['adb', 'shell', 'rm', '"%s/%s"' % (device_dir, "@file@")]
        else:
            exit()
        if len(clone_tbd_set):
            print("Deleting Following files from Device")
            counter = 1
            for i in clone_tbd_set:
                print("{:^3}. {:{col_width}.{col_width}}".format(counter, i, col_width=20),
                      end="\t" if counter % 4 != 0 else "\n", flush=True)
                counter += 1
            print()

            clone_proceed = input("Do you want to proceed? (y)es (default) /(n)o: ") or 'y'
            if clone_proceed == 'y' or clone_proceed == "Y":
                for i in clone_tbd_set:
                    print("Deleting ", device_dir + "/" + i)
                    # print(clone_cmd[:-1] + [clone_cmd[-1].replace("@file@", i)])
                    print(subprocess.check_output(clone_cmd[:-1] + [clone_cmd[-1].replace("@file@", i)]))
        else:
            exit()


"""Start of the Program"""

print("Searching and connecting to adb devices...")
devices = devices_print()
if devices == '-1':
    print("No device Found")
    more = True
else:
    print("\n".join(str(e) for e in iter(devices)))

more_msg = "\nWant to add network devices?(y)es/(n)o/(r)efresh: "

while devices_print() == '-1':
    add_more = input(more_msg) or 'n'
    if add_more == 'y' or add_more == 'Y':
        device_address = input("Enter address of the device (i.p.a.dd:port_number): ")
        device_add_status = subprocess.check_output(['adb', 'connect', device_address])
        print(device_add_status.decode('utf-8'))
        more_msg = 'Add more devices?(y)es/(n)o/(r)efresh: '
    elif add_more == 'r' or add_more == 'R':
        subprocess.call('adb kill-server'.split())
        subprocess.check_output('adb start-server'.split())
    elif add_more == 'n' and devices_print() == '-1':
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
    _ = input("Previously synced directory found \"%s\" for the device \"%s\" to sync with \"%s\".\n"
              "Want to sync it again?(y)es(default)/(n)o: " % (
              dir_arr[0], device_name, os.path.abspath(dir_arr[1]))) or 'y'
    if _ == 'y':
        directory = config_file[device_name]['device_directory']
        host_directory = config_file[device_name]['host_directory']
        where = 'a'
    else:
        where = 'c'
if not where:
    where = input("Directory: (c)ard(default)/(a)dvanced: ") or 'c'

if where == 'c':
    cards = list(
        enumerate(subprocess.check_output(['adb', '-s', device_name, 'shell', "ls|grep card"]).decode("utf-8").split()))
    for i in cards:
        print(i[0], '.', i[1])
    which_card = input("Which card?(0 default): ") or '0'
    which_card = int(which_card)
    directory.append(cards[which_card][1])

    print("Choose a directory in PC to sync with...")

    while True:
        dir_arr = [i[1] for i in list_dir('', parent=host_directory, device_type='1',
                                          listing_type='d', numerated=True, prints=True)]
        print("\n\t===\n\tCurrent Host directory",
              os.path.abspath("/".join(str(e) for e in host_directory)),
              "\n\t===")
        sub_search = input("\n\tChange directory? directory_index/(u)p /-1 -> done  (default): ") or '-1'
        if sub_search == '-1':
            break
        elif sub_search == 'u' or sub_search == 'U':
            host_directory = os.path.abspath(os.path.join("/".join(str(e) for e in host_directory),
                                                          os.pardir)
                                             ).split("/")
            continue
        sub_search = dir_arr[int(sub_search)]
        host_directory.append(sub_search)
    print("\nChoose a device directory to sync with...")
    while True:
        dir_arr = [i[1] for i in list_dir(device_name, parent=directory, device_type='0',
                                          listing_type='d', numerated=True, prints=True)]
        print("\n\t===\n\tCurrent Android directory",
              "/".join(str(e) for e in directory),
              "\n\t===")
        sub_search = input("\n\tChange directory? directory_index/(u)p /-1 -> done  (default): ") or '-1'
        if sub_search == '-1':
            break
        elif sub_search == 'u' or sub_search == 'U':
            directory = directory[:-1]
            continue
        sub_search = dir_arr[int(sub_search)]
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
