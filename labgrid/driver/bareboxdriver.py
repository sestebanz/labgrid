import attr

from ..factory import target_factory
from ..protocol import CommandProtocol, ConsoleProtocol, LinuxBootProtocol
from .common import Driver


@target_factory.reg_driver
@attr.s
class BareboxDriver(Driver, CommandProtocol, LinuxBootProtocol):
    """BareboxDriver - Driver to control barebox via the console"""
    bindings = {"console": ConsoleProtocol, }
    prompt = attr.ib(default="", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def run(self, cmd):
        pass

    def run_check(self, cmd):
        pass

    def get_status(self):
        pass

    def await_boot(self):
        pass

    def boot(self, name):
        pass