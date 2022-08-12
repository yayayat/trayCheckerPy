
from camera import Camera
from threading import Thread
import IO
import sys
import cv2
from time import sleep
from stream import ThreadedHTTPServer, CamHandler, Dashboard
import netifaces as ni
from processing import Processing, PROC_HEIGHT, PROC_WIDTH

IO.initialize()

TOLERANCE = 10
LONGSIDE = 320
SHORTSIDE = 230
THETA = 45
TRASH_THRESHOLD = 20
source = Camera()
proc = Processing(source)

board = Dashboard((PROC_HEIGHT*2, PROC_WIDTH*2 + 640, 3))

iface = sys.argv[1]
ip_addr = (ni.ifaddresses(iface)[ni.AF_INET][0]['addr'], 8080)

print("Starting server @ {}:{}".format(ip_addr[0], ip_addr[1]))

server = ThreadedHTTPServer(board, ip_addr, CamHandler)
print("server started")
server_poll = Thread(target=server.serve_forever, args=())
server_poll.start()
board.setFrame('background', proc.setBackground())
while True:
    request = IO.read()
    # print(request)
    if request == 0:
        IO.write(0)
    elif request == 1:
        board.setFrame('background', proc.setBackground())
        IO.write(3)
        print("Setting new background")
    elif request == 2:
        board.setFrame('main', proc.readFromSource())
        board.setFrame('main', proc.readFromSource())
        board.setFrame('transformed', proc.transform())
        dif, difColor = proc.subtractBackground()
        trash = cv2.mean(dif)
        board.setFrame('difference', difColor)
        pos, cont, _ = proc.findTray()
        board.setFrame('contours', cont)
        # print(pos[0] - LONGSIDE)
        # print(pos[1] - SHORTSIDE)
        if (trash[0] < TRASH_THRESHOLD):
            IO.write(3)
        elif((abs(pos[0] - LONGSIDE) < TOLERANCE) and
             (abs(pos[1] - SHORTSIDE) < TOLERANCE) and
             (pos[2] > THETA)):
            print("OK")
            IO.write(2)
        else:
            print("NOT OK")
            IO.write(1)
        print("Tray position is {}".format(pos))
    elif request == 3:
        board.setFrame('main', proc.readFromSource())
        board.setFrame('main', proc.readFromSource())
        board.setFrame('transformed', proc.transform())
        dif, difColor = proc.subtractBackground()
        pos, cont, box = proc.findTray()
        trash = cv2.mean(dif)
        difMask = cv2.fillPoly(dif, [box], (0, 0, 0))
        difColor = cv2.fillPoly(difColor, [box], (0, 0, 0))
        trashMask = cv2.mean(dif)
        board.setFrame('difference', difColor)
        board.setFrame('contours', cont)
        if (trash[0] < TRASH_THRESHOLD):
            IO.write(3)
        elif(not((abs(pos[0] - LONGSIDE) < TOLERANCE) and
             (abs(pos[1] - SHORTSIDE) < TOLERANCE) and
             (pos[2] > THETA) and
             (trashMask[0] < TRASH_THRESHOLD))):
            IO.write(2)
        else:
            IO.write(1)
        print("Tray position is {}".format(pos))
    board.render()
