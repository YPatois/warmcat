#!/usr/bin/env python3

import subprocess
import signal
import time

kTestMode=False

def start_shell_subprocess():
    if ( not kTestMode):
        # Start the virtual framebuffer first
        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '-nolisten', 'tcp'])

    # Start the actual load, use glxgears on display 99
    shell_process = subprocess.Popen(['glxgears', '-display', ':99'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Suspend and unsuspend the shell process every second
    while True:
        # Suspend the shell process
        shell_process.send_signal(signal.SIGTSTP)

        # Wait for 1 second
        time.sleep(4)

        # Resume the shell process
        shell_process.send_signal(signal.SIGCONT)

        # Wait for 1 second
        time.sleep(2)

start_shell_subprocess()

def main():
    start_shell_subprocess()

if __name__ == '__main__':
    main()
