#!/bin/python3

import json
import sys
import getopt
import subprocess
import os

def runCommand(command, path):
    RSP_STDOUT = "stdout"
    RSP_STDERR = "stderr"
    RSP_RETCODE = "ret_code"
    RSP_EXCEPTION = "exception"
    execResponse = {}
    try:
        execResponse[RSP_STDOUT] = \
            subprocess.check_output(
                command,
                encoding="utf-8",
                stderr=subprocess.STDOUT,
                cwd=path,
                shell=True)
        execResponse[RSP_RETCODE] = 0
    except subprocess.CalledProcessError as e:
        execResponse[RSP_RETCODE] = e.returncode
        # Note that because stderr has been redirected to
        # stdout, all output is contained in stdout
        execResponse[RSP_STDOUT] = e.stdout
    except Exception as e:
        execResponse[RSP_EXCEPTION] = e.strerror
    finally:
        outcome = True
        if execResponse[RSP_RETCODE] == 0:
            pass
        else:
            outcome = False
        if RSP_EXCEPTION in execResponse:
            return execResponse[RSP_EXCEPTION], False
        return execResponse[RSP_STDOUT], outcome

# get arguments user and server
argv = sys.argv[1:]
# print(argv)
opts, args = getopt.getopt(argv, "s:u:p:")
# print(opts)

if not opts:
    print("loginOcp.py -u <your_ocp_username> -p <password> -s <DEV-HQ|DEV-SHIP|PREPROD-HQ|PROD-HQ>")
    sys.exit(2)

for opt, arg in opts:
    if opt in ['-s']:
        # print("server is: " + arg)
        server = arg
    elif opt in ['-u']:
        # print("user is: " + arg)
        user = arg
    elif opt in ['-p']:
        password = arg

# this is the directory where the python script resides
scriptPath = os.path.join(os.path.dirname(os.path.realpath(__file__)))

# opening JSON file and load its content
data = json.load(open(scriptPath + "/ocpUrl.json"))

for key in data.keys():
    if key == server:
        loginServer = data[key]
    elif key == "password":
        # if not set in command line, try to get pwd from json
        password = data["password"]
    elif key == "user":
        # if not set in command line, try to get user from json
        user = data["user"]
try:
    loginServer
    password
except NameError:
    print("loginOcp.py -u <your_ocp_username> -p <password> -s <DEV-HQ|DEV-SHIP|PREPROD-HQ|PROD-HQ>")
    sys.exit(2)

command = f"oc login --username={user} --server={loginServer} --password={password}"
commandOutput = f"oc login --username={user} --server={loginServer}"
print(commandOutput)

result, outcome = runCommand(command, path='.')
if not outcome:
    print(f'error on login to: {loginServer} - error is: {result}')
else:
    print("Login Success!")
