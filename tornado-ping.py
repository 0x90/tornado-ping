#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Tornado ping example

__author__ = '090h'
__license__ = 'GPL'

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, asynchronous
from subprocess import Popen, PIPE, STDOUT
from tornado.gen import Task, engine
from os import path
from tornado.log import enable_pretty_logging


class SyncHandler(RequestHandler):

    @asynchronous
    @engine
    def get(self):
        self.post()

    @asynchronous
    @engine
    def post(self):
        host = self.get_argument("host", default="ya.ru")
        # Use list insted of command string to prevent command injection
        cmd = ['ping', '-c', '5', host]
        result = yield Task(self.subprocess, cmd)
        self.finish(result)

    def subprocess(self, cmd, callback):
        ioloop = IOLoop.instance()
        pipe = Popen(cmd, stdin=PIPE, stdout=PIPE,
                        stderr=STDOUT, close_fds=True)
        fd = pipe.stdout.fileno()
        result = []

        def recv(*args):
            data = pipe.stdout.readline()
            if data:
                result.append(data)
            elif pipe.poll() is not None:
                ioloop.remove_handler(fd)
                callback('<br>'.join(result))

        ioloop.add_handler(fd, recv, ioloop.READ)

class AsyncHandler(RequestHandler):

    def get(self):
        self.post()

    @asynchronous
    def post(self):
        host = self.get_argument("host", default="ya.ru")
        print('async. host: %s' % host)
        # Use list insted of command string to prevent command injection
        cmd = ['ping', '-c', '5', host]

        def send(data):
            if data:
                self.write(data+'<br>')
                self.flush()
            else:
                self.write('process finished!')
                self.finish()

        self.subprocess(cmd, send)

    def subprocess(self, cmd, callback):
        ioloop = IOLoop.instance()
        pipe = Popen(cmd, stdin=PIPE, stdout=PIPE,
                            stderr=STDOUT, close_fds=True)
        fd = pipe.stdout.fileno()

        def recv(*args):
            data = pipe.stdout.readline()
            if data: callback(data)
            elif pipe.poll() is not None:
                ioloop.remove_handler(fd)
                callback(None)

        # read handler
        ioloop.add_handler(fd, recv, ioloop.READ)



class MainHandler(RequestHandler):

    def get(self):
        self.render('index.html')


def main():
    handlers = [
        (r"/", MainHandler),
        (r"/sync/", SyncHandler),
        (r"/async/", AsyncHandler),
    ]

    ssl = {
        "certfile": path.join("certs/server.crt"),
        "keyfile": path.join("certs/server.key"),
    }

    enable_pretty_logging()

    http_server = HTTPServer(Application(handlers, debug=True), ssl_options=ssl,)
    print('Open https://127.0.0.1:8443')
    http_server.listen(8443)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()