import sys
import subprocess

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

def printDeployments():

    # get OCP project
    command = "oc project -q"
    project, outcome = runCommand(command, path='.')
    if not outcome:
        print(f'cannot get deployments list')
        print(f'error is: {project}')
        sys.exit(2)

    # get list of deployment
    command = "oc get deployment | awk '{print $1}' | grep -v NAME"
    listDeployment, outcome = runCommand(command, path='.')
    if not outcome:
        print(f'cannot get deployments list')
        print(f'error is: {listDeployment}')
        sys.exit(2)

    print("")
    print(f"Current namespace is: {project}")
    print(f"Deployment available are:")
    for deployment in listDeployment.splitlines():
        print("- " + deployment)


def restartDeployment(deployment):

    # get list of deployment
    command = "oc get deployment | awk '{print $1}' | grep -v NAME"
    listDeployment, outcome = runCommand(command, path='.')
    if not outcome:
        print(f'cannot get deployments list')
        print(f'error is: {listDeployment}')
        sys.exit(2)

    if deployment in listDeployment:

        command = f"oc get deployment {deployment} -o yaml | shyaml get-value spec.replicas"
        replicas, outcome = runCommand(command, path='.')
        if not outcome:
            print(f'cannot get replicas info from deployment {deployment}')
            print(f'error is: {replicas}')
            sys.exit(2)
        print(f'{deployment} - replicas: {replicas}')

        answer = input("Do you want to proceed with restart? [Y/N]: ")
        if answer == "Y":
            command = f"oc scale deployment {deployment} --replicas=0"
            output, outcome = runCommand(command, path='.')
            if not outcome:
                print(f'cannot scale down deployment {deployment}')
                print(f'error is: {output}')
                sys.exit(2)
            else:
                print(f'{deployment} scaled to 0')

            command = f"oc scale deployment {deployment} --replicas={replicas}"
            output, outcome = runCommand(command, path='.')
            if not outcome:
                print(f'cannot scale up deployment {deployment} to {replicas} replicas')
                print(f'error is: {output}')
                sys.exit(2)
            else:
                print(f'{deployment} scaled to {replicas} replicas')

    else:
        print(deployment + " is not a deployment")
        sys.exit(2)


def printActions():
    prompt = """
    Select the action:
    [1] Restart a deployment
    [2] Quit
    """
    print(prompt)

while True:

    printActions()
    yourChoise = str(input("Action: "))

    if yourChoise == "1":
        printDeployments()
        deployment = input("Which deployment do you want to restart? ")
        restartDeployment(deployment)
    elif yourChoise == "2":
        sys.exit()
