#!/usr/bin/python3
"""
   Author: Igor Maculan - n3wtron@gmail.com
   A Simple mjpg stream http server
"""


import cv2
import http
from threading import Lock
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import time
import numpy as np


class CamHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        img_src = 'http://{}:{}/cam.mjpg'.format(
            server.server_address[0], server.server_address[1])
        self.html_page = """
            <html>
                <head></head>
                <body>
                    <img src="{}"/>
                </body>
            </html>""".format(img_src)
        self.html_404_page = """
            <html>
                <head></head>
                <body>
                    <h1>NOT FOUND</h1>
                </body>
            </html>"""
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(http.HTTPStatus.OK)
            self.send_header(
                'Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                try:
                    img = self.server.source.read()
                    retval, jpg = cv2.imencode('.jpg', img)
                    if not retval:
                        raise RuntimeError('Could not encode img to JPEG')
                    jpg_bytes = jpg.tobytes()
                    self.wfile.write("--jpgboundary\r\n".encode())
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(jpg_bytes))
                    self.end_headers()
                    self.wfile.write(jpg_bytes)
                    time.sleep(self.server.read_delay)
                except (IOError, ConnectionError):
                    break
        elif self.path.endswith('.html'):
            self.send_response(http.HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.html_page.encode())
        else:
            self.send_response(http.HTTPStatus.NOT_FOUND)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.html_404_page.encode())


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

    def __init__(self, source, server_address, RequestHandlerClass, bind_and_activate=True):
        HTTPServer.__init__(self, server_address,
                            RequestHandlerClass, bind_and_activate)
        ThreadingMixIn.__init__(self)
        fps = 30.
        self.read_delay = 1. / fps
        self.source = source

    def serve_forever(self, poll_interval=0.5):
        try:
            super().serve_forever(poll_interval)
        except KeyboardInterrupt:
            pass
            # self._camera.release()


class Dashboard:
    # {'main':0,'transformed':0,'background':0,'difference':0,'contours':0}
    _lk = Lock()
    _frames = dict()

    def __init__(self, shape):
        self._img = np.zeros(shape, np.uint8)

    def read(self):
        with self._lk:
            return self._img

    def render(self):
        with self._lk:
            # output[0: procHeight, 0: procWidth] = transformed
            if 'main' in self._frames:
                shape = self._frames['main'].shape
                self._img[0: shape[0], 0: shape[1]] = self._frames['main']
            if 'transformed' in self._frames:
                shape = self._frames['transformed'].shape
                self._img[0: shape[0], 640: 640 + shape[1]
                          ] = self._frames['transformed']
            if 'background' in self._frames:
                shape = self._frames['background'].shape
                self._img[0: shape[0], 640 + shape[1]: 640 + shape[1]
                          * 2] = self._frames['background']
            if 'difference' in self._frames:
                shape = self._frames['difference'].shape
                self._img[shape[0]: shape[0]*2, 640: 640 +
                          shape[1]] = self._frames['difference']
            if 'contours' in self._frames:
                shape = self._frames['contours'].shape
                self._img[shape[0]: shape[0]*2, 640 + shape[1]
                    : 640 + shape[1] * 2] = self._frames['contours']
            # buf = cv2.cvtColor(diffBlur, COLOR_GRAY2BGR)
            # output[procHeight: procHeight*2, 0: procWidth] = buf[blackSpaces: blackSpaces +
            #                                                      procHeight, blackSpaces: blackSpaces+procWidth]
            # buf = cv2.cvtColor(difference, COLOR_GRAY2BGR)
            # output[0: procHeight, procWidth: procWidth*2] = buf[blackSpaces: blackSpaces +
            #                                                     procHeight, blackSpaces: blackSpaces+procWidth]
            # buf = cv2.cvtColor(cont, COLOR_RGB2BGR)
            # output[procHeight: procHeight*2, procWidth: procWidth *
            #        2] = buf[0: procHeight, 0: procWidth]
            # imgRGB = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    def setFrame(self, N, img):
        with self._lk:
            self._frames[N] = img
