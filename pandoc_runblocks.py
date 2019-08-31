#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import queue
import shlex
import subprocess
import threading

import pandocfilters as pdf
import psutil

__version__ = "0.1.0.dev"


class Interpreter(object):
    def __init__(self, exec):
        self.popen = subprocess.Popen(
            shlex.split(exec),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.process = psutil.Process(self.popen.pid)
        self.queue = queue.Queue()
        self.readthread = threading.Thread(
            target=self.queue_output, daemon=True
        )
        self.readthread.start()

    def queue_output(self):
        while True:
            for char in iter(lambda: self.popen.stdout.read(1), ""):
                self.queue.put(char)

    def communicate(self, input):
        self.popen.stdin.write(input)
        self.popen.stdin.write("\n")
        self.popen.stdin.flush()
        response = []
        while True:
            try:
                nextline = self.queue.get(timeout=0.5)
                response.append(nextline)
            except queue.Empty:
                if not self.process.status() == psutil.STATUS_RUNNING:
                    break
        while not self.queue.empty():
            response.append(self.queue.get())
        return "".join(response)


class PythonInterpreter(Interpreter):
    def __init__(self):
        super().__init__(exec="python -qi")


INTERPRETERS = {"python": PythonInterpreter}


class Environment(object):
    def __init__(self):
        self.interpreters = {}

    def convert(self, key, value, format, meta):
        if key == "CodeBlock":
            (ident, classes, keyvals), code = value
            try:
                fmt = [i for i in classes if i in INTERPRETERS][0]
            except IndexError:
                return
            try:
                interpreter = self.interpreters[fmt]
            except KeyError:
                self.interpreters[fmt] = INTERPRETERS[fmt]()
                interpreter = self.interpreters[fmt]
            text = interpreter.communicate(code)
            return [pdf.CodeBlock(*value), pdf.CodeBlock(("", [], []), text)]


def main():
    environment = Environment()
    pdf.toJSONFilter(environment.convert)


if __name__ == "__main__":
    main()