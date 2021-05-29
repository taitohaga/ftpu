# FTP-Uploader
# a simple file uploader via FTP by Taito Haga

"""
python path/to/ffft.py [operation] <option>

[operation]:
    connect: make the current directory be connected to a server. starts setting guide.

    update [-u|-d] <files>: update the scecified files at one time.
        If <files> not given, update all the files in the project directory.

        -u: only upload files.
        -d: only delete files which have been already deleted in the local.

"""

import sys, os, json, glob
from getpass import getpass
from ftplib import FTP

# detect binary or text.
# It is difficult to detect the filetype but this is_binary just consider files with the particular expansions as "text" or "binary"!
TEXT_EXPANSIONS = ["txt", "html", "htm", "md", "py", "csv", "php"]
def is_binary(filename: str):
    for exp in TEXT_EXPANSIONS:
        if filename.endswith(exp):
            return False
    return True

# path to config file
CONFIG_PATH = "ffftpy-config.json"

def get_config_path(specified=""):
    home = os.environ.get("HOME")
    if home is None:
        home = os.path.expanduser("~")
    if specified == "":
        config_path = os.path.join(home,CONFIG_PATH)
    else:
        config_path = os.path.join(specified, CONFIG_PATH)
    return config_path

# get configurations required for connecting to the host
# if the json file does not exist, create it on home directory.
def get_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, mode="r") as f:
            config = json.load(f)
        return config
    else:
        print("config file does not exist.")
        print("config file being created...")
        with open(config_path, mode="w") as f:
            template_json = {}
            json.dump(template_json, f)
        return template_json

def save_config(config_path, config):
    if os.path.exists(config_path):
        with open(config_path, mode="w") as f:
            json.dump(config, f)
        return
    print("Error: config file was deleted while executing. config was not saved.")

class FTPUploader():

    def __init__(self, config: dict, config_path):
        self.config = config
        self.CONFIG_PATH = config_path

    def _is_connected(self):
        current = os.getcwd()
        if current in self.config.keys():
            return True
        else:
            return False

    def _get_ftp(self):
        entry = self.config[os.getcwd()]
        return FTP(entry["host"], entry["user"], entry["password"])

    # register the current directory and connect to the host.
    def connect(self):
        current = os.getcwd()
        
        for k in self.config.keys():
            if k == current:
                print("Err: this directory has been already registered.")
                return 1
            elif k in current:
                print("Err: cannot register the subdirectory whose parent is already registered to the config.")
                return 1

        entry = {}
        
        host = user = password = ""

        while host == "" or user == "" or password == "":
            host = input("Host server name: ")
            user = input("User name: ")
            password = getpass("Password for %s: " % user)

        entry["host"] = host
        entry["user"] = user
        entry["password"] = password

        print("You can specify where to locate your project directory in on the server.")
        print("If not specified, the directory is set root directory.")
        project_root_dir = input("Directory: ")
        if project_root_dir == "":
            project_root_dir = "/"
        entry["project_root_dir"] = project_root_dir

        print(current, "will be connected to", entry["host"])
        self.config[current] = entry
        return 0

    def _update_create(self, files, ftp):
        created = 0
        updated = 0
        entry = self.config[os.getcwd()]
        prev_dirpath = ""
        for path in files:
            dirpath, basepath = os.path.split(path)

            if dirpath != prev_dirpath:
                # split the full path, go to the target.
                # if the subdirectories do not exist, make them all.
                ftp.cwd(entry["project_root_dir"])
                direction = dirpath.split(os.sep)
                for dirname in direction:
                    dirs = [filename for filename, opt in ftp.mlsd(facts=["type"]) if opt["type"].endswith("dir")]
                    if not dirname in dirs:
                        ftp.mkd(dirname)
                        print("Created directory:", dirpath)
                    ftp.cwd(dirname)

            # now sure ftp.pwd() is in `basepath`
            with open(path, mode="rb") as f:
                is_new = basepath in ftp.nlst()
                if is_binary(path):
                    ftp.storbinary("STOR %s" % basepath, f)
                else:
                    ftp.storlines("STOR %s" % basepath, f)
                if is_new:
                    print("Updated:", path)
                    updated += 1
                else:
                    print("Created:", path)
                    created += 1

            prev_dirpath = dirpath
        return created, updated

    def _update_delete(self, ftp):
        entry = self.config[os.getcwd()]
        deleted = 0

        def explore(filename, dir_only, followed_by_parent):
            filelist = ftp.mlsd(path=filename, facts=["type"])
            for f, opt in filelist:
                if opt["type"] == "file":
                    if not dir_only:
                        yield f
                if opt["type"] == "dir":
                    if followed_by_parent:
                        for name in explore(filename + f + "/", dir_only=dir_only, followed_by_parent=followed_by_parent):
                            yield f + "/" + name
                        yield f + "/"
                    else:
                        yield f + "/"
                        for name in explore(filename + f + "/", dir_only=dir_only, followed_by_parent=followed_by_parent):
                            yield f + "/" + name

        # delete server files already deleted in local
        for name in explore(entry["project_root_dir"], dir_only=False, followed_by_parent=False):
            if not name.endswith("/") and not os.path.exists(os.path.join(os.getcwd(), name)):
                ftp.delete(entry["project_root_dir"] + name)
                deleted += 1
                print("Deleted:", name)

        # delete server directories already deleted in local when they have no files or subdirs.
        for name in explore(entry["project_root_dir"], dir_only=True, followed_by_parent=True):
            if not os.path.exists(os.path.join(os.getcwd(), name)):
                if len(ftp.nlst(entry["project_root_dir"] + name)) == 2:
                        ftp.rmd(entry["project_root_dir"] + name)
                        print("Directory deleted:", name)

        return deleted

    def update(self, files, shortcut):
        if not self._is_connected():
            print("This directory is not connected to any server. Please use `connect` command before")
            return 1
        ftp = self._get_ftp()

        if shortcut == "upload_only":
            created, updated = self._update_create(files, ftp)
            deleted = 0
        elif shortcut == "delete_only":
            created= updated = 0
            deleted = self._update_delete(ftp)
        else:
            created, updated = self._update_create(files, ftp)
            deleted = self._update_delete(ftp)

        # print the log
        print("Successfully updated. (created: %d, updated: %d, deleted: %d)" 
                % (created, updated, deleted))
        return 0

    def _get_ignore_list(self, ignore_path=""):
        if ignore_path == "":
            ignore_path = os.path.join(".", "ignores")
        ignore_list = []
        if not os.path.exists(ignore_path):
            return ignore_list
        ignore_list.append(ignore_path)
        with open(ignore_path, mode="r") as f:
            for ig_line in f.readlines():
                ig_line = os.path.join(".", ig_line).strip()
                for ig in self._get_filelist([ig_line]):
                    ignore_list.append(ig)
        return ignore_list

    def _get_filelist(self, pathlist):
        filelist = []
        for path in pathlist:
            if not os.path.exists(path):
                print("Warning: specified path %s is not found. Will be ignored." % path)
            if os.path.isfile(path):
                filelist.append(path)
            elif os.path.isdir(path):
                for p in glob.glob("%s/**/*" % path, recursive=True):
                    if os.path.isfile(p):
                        filelist.append(p)
        return filelist

    def _parse(self):
        words = sys.argv[1:]
        if len(words) == 0:
            return {"ErrorMsg": "requires any operation command"}
        command = {}
        command["operation"] = words[0]
        
        if command["operation"] == "update":
            ignore_list = self._get_ignore_list()
            command["shortcut"] = "both"
            if len(words) > 1:
                if words[1] == "-d":
                    command["shortcut"] = "delete_only"
                    to_update = []
                elif words[1] == "-u":
                    command["shortcut"] = "upload_only"
                    to_update = [f for f in self._get_filelist(words[2:])
                            if not f in ignore_list]
                else:
                    to_update = [f for f in self._get_filelist(words[1:])
                            if not f in ignore_list]
                    
                command["files"] = to_update
            else:
                to_update = [f for f in self._get_filelist(["."])
                    if not f in ignore_list]
                command["files"] = to_update

        command["ErrorMsg"] = ""
        return command

    def main(self):
        command = self._parse()

        if command["ErrorMsg"] != "":
            print(command["ErrorMsg"])
            return 1
        
        if command["operation"] == "connect":
            result = self.connect()
        elif command["operation"] == "update":
            result = self.update(command["files"], shortcut=command["shortcut"])
        else:
            print("Err: command %s is invalid" % command["operation"])
            result = 1
        return result

config = get_config(get_config_path())
ftpu = FTPUploader(config, CONFIG_PATH)
result = ftpu.main()
print("Result:", result)
if result == 0:
    save_config(get_config_path(), ftpu.config)
