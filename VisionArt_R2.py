import cv2
import imutils
import numpy as np
import random as rnd 
import sys
import serial
from time import time, sleep

################################################################################ 
####################### Identificador de Formas ################################
################################################################################

class ShapeDetector:
    def __init__(self):
        pass
    def detect(self, c):
        #inicializa el nombre de la forma y su contorno aproximado
        shape = 'No identificado'
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04*peri, True)
        #Si es un triangulo, tiene 3 vertices
        if len(approx) == 3:
            shape = 'Triangulo'
        elif len(approx) == 4:
            (x,y,w,h) = cv2.boundingRect(approx)
            ar = w / float(h)
            shape = 'Cuadrado' if ar >= 0.95 and ar <= 1.05 else 'Rectangulo'
        elif len(approx) == 5:
            shape = 'Pentagono'
        else:
            if len(approx) == 6:
                shape = 'Indicador'
            elif len(approx) == 10:
                shape = 'Estrella'
            else:
                shape = 'Circulo'
        return shape

 
################################################################################ 
####################### Conversion ASCII #######################################
################################################################################

def text2ASCII(texto):
    i = 0
    Size = len(texto)
    Temp = ''
    while i < Size:
        Temp += str(ord(texto[i]))
        i += 1
    return Temp

def list2string(list):
  string=""
  string=string.join(list)
  string=string + "\r\n"
  return string
 
################################################################################ 
####################### Carga de imagenes ######################################
################################################################################

framewidth = 640
frameheight = 480
cap = cv2.VideoCapture("video3.mp4")
cap.set(3, framewidth)
cap.set(4, frameheight)

################################################################################ 
####################### Ventana de Parametros ##################################
################################################################################

def empty(a):
    pass
cv2.namedWindow("Parameters")
cv2.resizeWindow("Parameters", 640, 240)
cv2.createTrackbar("Threshold1", "Parameters", 200, 255, empty)
cv2.createTrackbar("Threshold2", "Parameters", 200, 255, empty)
cv2.createTrackbar("Area Minima", "Parameters", 1700, 30000, empty)
## Juntar imágenes en
def stackImages(scale,imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver

################################################################################ 
############################## Contornos  ######################################
################################################################################


def getContours(imgDil, img):
    contours, hier = cv2.findContours(imgDil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        #centro del contorno, luego detecta la forma
        M = cv2.moments(c)
        #Coord de la figura
        cX = int( (M["m10"] / M["m00"]) * ratio)
        cY = int ( (M["m01"] / M["m00"]) * ratio)
        area = cv2.contourArea(c)
        areaMin = cv2.getTrackbarPos("Area Minima", "Parameters")
        if area > areaMin:
            shape = sd.detect(c)
            # multiplica las coords del contorno (x,y) por el radio, dibuja contornos y el nombre de la fig
            c = c.astype("float")
            c *= ratio
            c = c.astype('int')
            cv2.drawContours(img, [c], -1, (0,255,0), 2)
            cv2.putText(img, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
            info_normal.append([shape, (cX, cY)])
            info_ascii.append([text2ASCII(shape), (chr(cX), chr(cY))])
    ser_ascii = [ str(info_ascii) +','+ str(info_ascii) +';']
    ser_ascii = list2string(ser_ascii) # Coordenadas concatenadas
    print('Identificador y Par de coordenadas:\n\t', ser_ascii)
    print('Informacion Concatenadas:\n\t' + ser_ascii)
    print('Tamaño de la cadena ASCII: {} bytes '.format(sys.getsizeof(ser_ascii)))
    info_ascii.clear()

################################################################################ 
####################### Filtros y salidas ######################################
################################################################################
def checkDuplicate(lista):
    if len(lista)==len(set(lista)): # False si hay repetido
        return False
    else:
        return True

info_normal = []
info_ascii = []
cont = 0
sd = ShapeDetector()
while True:
    ret, img = cap.read()
    ratio = img.shape[0] / float(img.shape[0])
    imgContour = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgblur = cv2.GaussianBlur(imgGray, (7,7), 0)
    
    threshold1 = cv2.getTrackbarPos("Threshold1", "Parameters")
    threshold2 = cv2.getTrackbarPos("Threshold2", "Parameters")
    imgCanny = cv2.Canny(imgblur, threshold1, threshold2)
    kernel = np.ones((5,5))
    imgDil = cv2.dilate(imgCanny, kernel, iterations = 1)
    thresh = cv2.threshold(imgDil,150, 255, cv2.THRESH_BINARY)[1]
    getContours(thresh, imgContour)
    img_stacked = stackImages(0.5,([img,imgContour,imgCanny], [imgDil, thresh, thresh]))
    cv2.imshow("Titulo", img_stacked)

    #ser_ascii = [ ( str(info_ascii[j][0]) +','+ str(info_ascii[j][1]) +';') for j in range(len(info_ascii)) ]  
    cont += 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
    #sleep(0.5 - time() % 0.5) # Esto es para que haga todo cada medio segundo!!!
    
