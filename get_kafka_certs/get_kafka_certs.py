import sys
import os
import subprocess
import tempfile
import json

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

# opening JSON file and load its content
data = json.load(open("kafkaInput.json"))

# get 7 variables from json file
certPass = data["certificate_password"]
namespace = data["kafka_namespace"]
clusterCaCertSecret = data["secret_clusterCaCert"]
clusterCaSecret = data["secret_clusterCa"]
pemCert = data["pem_certificate"]
keyCert = data["key_certificate"]
destAlias = data["destination_alias"]

# create ad-hoc directory, kafkaPath will be used as runCommand argument
kafkaPath = tempfile.mkdtemp()
print("")
print("--->  All outputs will be written into directory " + kafkaPath + " <----")
print("")

# this is the directory where the python script resides
scriptPath = os.path.join(os.path.dirname(os.path.realpath(__file__)))

# create an empty list
commands = [None]*13

# extract internal certs from kafka namespace
commands[0] = f"oc project {namespace}"
commands[1] = f"oc extract secret/{clusterCaCertSecret} --keys=ca.crt --to=- > ca.pem"
commands[2] = f"oc extract secret/{clusterCaSecret} --keys=ca.key --to=- > ca.key"

# create internal certs
commands[3] = f"openssl pkcs12 -export -in ca.pem -inkey ca.key -out fullchain.pkcs12 -password pass:{certPass}"
commands[4] = f"keytool -v -importkeystore -srckeystore fullchain.pkcs12 -destkeystore keystore.jks -deststoretype JKS -deststorepass {certPass} -srcstorepass {certPass}"
commands[5] = f"keytool -keystore keystore.jks -changealias -alias 1 -destalias kafka-internal-cert -storepass {certPass}"
commands[6] = f"keytool -v -importkeystore -srckeystore fullchain.pkcs12 -destkeystore truststore.jks -deststoretype JKS -deststorepass {certPass} -srcstorepass {certPass}"
commands[7] = f"keytool -keystore truststore.jks -changealias -alias 1 -destalias kafka-internal-cert -storepass {certPass}"

# create external certs
commands[8] = f"openssl pkcs12 -export -in {pemCert} -inkey {keyCert} -out fullchain.pkcs12 -password pass:{certPass}"
commands[9] = f"keytool -v -importkeystore -srckeystore fullchain.pkcs12 -destkeystore keystore.jks -deststoretype JKS -deststorepass {certPass} -srcstorepass {certPass}"
commands[10] = f"keytool -keystore keystore.jks -changealias -alias 1 -destalias {destAlias} -storepass {certPass}"
commands[11] = f"keytool -v -importkeystore -srckeystore fullchain.pkcs12 -destkeystore truststore.jks -deststoretype JKS -deststorepass {certPass} -srcstorepass {certPass}"
commands[12] = f"keytool -keystore truststore.jks -changealias -alias 1 -destalias {destAlias} -storepass {certPass}"

for command in commands:
    result, outcome = runCommand(command, path=kafkaPath)
    print(f"# command succeded: [{outcome}] - result is {result}")
    if not outcome:
        sys.exit()

print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
print("Procedure is complete! Your keystore file content is:")
print("")
command = f"keytool -list -keystore keystore.jks -storepass {certPass}"
result, outcome = runCommand(command, path=kafkaPath)
print(result)
print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
print("")

# let's encode keystore and truststore into base64

base64Commands = [None]*2

base64Commands[0] = "base64 -w 0 -i keystore.jks > keystore_base64.txt"
base64Commands[1] = "base64 -w 0 -i truststore.jks > truststore_base64.txt"

for command in base64Commands:
    result, outcome = runCommand(command, path=kafkaPath)
    if not outcome:
        print(f'cannot decode certificate into base64')
        print(f'error is: {result}')
        sys.exit()
    else:
        print(f'# command: ' + command + ' is OK')

print("")
print(f"---> Now you can copy the content of {kafkaPath}/keystore_base64.txt and {kafkaPath}/truststore_base64.txt in OCP Otalio Secret <----")