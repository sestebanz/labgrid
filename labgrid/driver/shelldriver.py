import logging
import re
import shlex

import attr
from pexpect import TIMEOUT

from ..factory import target_factory
from ..protocol import CommandProtocol, ConsoleProtocol
from .common import Driver
from .exception import ExecutionError


@target_factory.reg_driver
@attr.s
class ShellDriver(Driver, CommandProtocol):
    """ShellDriver - Driver to execute commands on the shell"""
    bindings = {"console": ConsoleProtocol, }
    prompt = attr.ib(validator=attr.validators.instance_of(str))
    login_prompt = attr.ib(validator=attr.validators.instance_of(str))
    username = attr.ib(validator=attr.validators.instance_of(str))
    password = attr.ib(default="", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.re_vt100 = re.compile(
            '(\x1b\[|\x9b)[^@-_a-z]*[@-_a-z]|\x1b[@-_a-z]'
        )  #pylint: disable=attribute-defined-outside-init,anomalous-backslash-in-string
        self.logger = logging.getLogger("{}:{}".format(self, self.target))
        self._status = 0  #pylint: disable=attribute-defined-outside-init
        self.await_login()
        self._check_prompt()
        self._inject_run()

    def run(self, cmd):
        """
        Runs the specified cmd on the shell and returns the output.

        Arguments:
        cmd - cmd to run on the shell
        """
        # FIXME: Handle pexpect Timeout
        cmp_command = '''run {}'''.format(shlex.quote(cmd))
        if self._status == 1:
            self.console.sendline(cmp_command)
            before, _, _ = self.console.expect(self.prompt)
            # Remove VT100 Codes and split by newline
            data = self.re_vt100.sub(
                '', before.decode('utf-8'), count=1000000
            ).split('\r\n')
            self.logger.debug("Received Data: %s", data)
            # Remove first element, the invoked cmd
            data = data[data.index("MARKER") + 1:]
            data = data[:data.index("MARKER")]
            exitcode = int(data[-1])
            del (data[-1])
            return (data, [], exitcode)
        else:
            return None

    def await_login(self):
        """Awaits the login prompt and logs the user in"""
        self.console.sendline("")
        try:
            self.console.expect(self.login_prompt)
        except TIMEOUT:
            pass
        self.console.sendline(self.username)
        if self.password:
            try:
                self.console.expect("Password: ")
            except TIMEOUT:
                pass
            self.console.sendline(self.password)

    def run_check(self, cmd):
        """
        Runs the specified cmd on the shell and returns the output if successful,
        raises ExecutionError otherwise.

        Arguments:
        cmd - cmd to run on the shell
        """
        res = self.run(cmd)
        if res[2] != 0:
            raise ExecutionError(cmd)
        return res[0]

    def get_status(self):
        """Returns the status of the shell-driver.
        0 means not connected/found, 1 means shell
        """
        return self._status

    def _check_prompt(self):
        """
        Internal function to check if we have a valid prompt
        """
        self.console.sendline("")
        try:
            self.console.expect(self.prompt)
            self._status = 1
        except TIMEOUT:
            self._status = 0

    def _inject_run(self):
        self.console.sendline(
            '''run() { echo "MARKER"; sh -c "$@"; echo "$?"; echo "MARKER"; }'''
        )
        self.console.expect(self.prompt)

    def cleanup(self):
        self.console.sendline("exit")
