from cv2 import cv2
import numpy as np

def stackImages(imgArray,scale,labels=[]):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
            hor_con[x] = np.concatenate(imgArray[x])
        ver = np.vstack(hor)
        ver_con = np.concatenate(hor)
    else:
        for x in range(0, rows):
            imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        hor_con= np.concatenate(imgArray)
        ver = hor
    if len(labels) != 0:
        eachImgWidth= int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)
        for d in range(0, rows):
            for c in range (0,cols):
                cv2.rectangle(ver,(c*eachImgWidth,eachImgHeight*d),(c*eachImgWidth+len(labels[d][c])*13+27,30+eachImgHeight*d),(255,255,255),cv2.FILLED)
                cv2.putText(ver,labels[d][c],(eachImgWidth*c+10,eachImgHeight*d+20),cv2.FONT_HERSHEY_COMPLEX,0.7,(255,0,255),2)
    return ver


def recContour(contours):
    recCon = []

    for i in contours:
        area = cv2.contourArea(i)

        if area > 60000:
            perimeter = cv2.arcLength(i, True)
            approximation = cv2.approxPolyDP(i, 0.02 * perimeter, True)
            #print("Corner Points", len(approximation)) #The ones with 4 are essentially a square or rectangle
            if len(approximation) == 4:
                recCon.append(i)
    # recCon = sorted(recCon, key = cv2.contourArea, reverse=True)

    return recCon

def getCornerPoints(cont):
    perimeter = cv2.arcLength(cont, True)
    approximation = cv2.approxPolyDP(cont, 0.02 * perimeter, True)
    return approximation

def reorder(myPoints):

    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4,1,2), np.int32)

    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)] #[0, 0]
    myPointsNew[3] = myPoints[np.argmax(add)] #[w, h]

    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] = myPoints[np.argmin(diff)] #[w, 0]
    myPointsNew[2] = myPoints[np.argmax(diff)] #[0, h]

    return myPointsNew

# def splitBoxes(img, questions, choices):
#     i = 0
#     rows = np.vsplit(img, questions) #this depends on imaage size and num of q/cols
#     cv2.imshow("row", rows[0])
#     boxes = []
#     # for r in rows:
#     #     cols = np.hsplit(r, choices)
#     #     for box in cols:
#     #         cv2.imshow('tester' + str(i), box )
#     #         boxes.append(box)
#     #         i = i +1
#     # print(len(boxes))
#     return boxes

def splitBoxes(img, questions, choices):
    print(questions)
    i = 0
    rows = np.vsplit(img, questions) #TODO 20 per box but we have 60 qs in total not as simple as passing in num off questions
    boxes = []
    for r in rows:
        cols = np.hsplit(r, choices)
        for box in cols:
            boxes.append(box)
            cv2.imshow("split" + str(i) , box)
            i = i + 1
    return boxes

def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index1
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
        key=lambda b:b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return (cnts)

