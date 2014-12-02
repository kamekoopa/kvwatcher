# -*- coding: utf-8 -*-


class Command(object):

    def __init__(self, command):
        u"""
        @type command : str
        """

        self.command = command

    def execute(self, stdin=None):
        u"""
        @type stdin : dict
        @rtype (int, str, str)
        """
        import json
        import shlex
        import subprocess
        from subprocess import PIPE

        command = shlex.split(self.command)
        process = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate(None if stdin is None else json.dumps(stdin))
        ret_code = process.wait()

        return ret_code, out, err
