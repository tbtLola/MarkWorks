import numpy
from django.http import HttpResponse
from cv2 import cv2
import numpy as np

from . import utils
import json
from django.core.files.storage import default_storage, settings
from django.core.files.base import ContentFile
from .forms import UploadForms

path = "Examinate/2.jpg"
widthImg = 700
heightImg = 700
questions = 5
choices = 5
answerKey = [1,2,0,1,4]



def scan_file(request):

#    if request.method == "POST":
  #  if request.method == 'POST':
    form = UploadForms(request.POST, request.FILES)
    file = request.FILES['file']
    path = default_storage.save()
    img = cv2.imread(path)

    print(file.name)
    HttpResponse("WOOHOO")

    img = cv2.resize(img, (widthImg, heightImg))
    imgContours = img.copy()
    imgMaxContours = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 50)

    # Finding all contours
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)

    # Find rectangles
    recContours = utils.recContour(contours)
    maxContour = utils.getCornerPoints(recContours[0])  # biggest contour

    print(maxContour.shape)
    gradingPoints = utils.getCornerPoints(recContours[1])
    # print(getCornerPoints(maxContour))
    if maxContour.size != 0 and gradingPoints.size != 0:
        cv2.drawContours(imgMaxContours, maxContour, -1, (0, 255, 0), 20)
        cv2.drawContours(imgMaxContours, gradingPoints, -1, (255, 0, 0), 20)

        maxContour = utils.reorder(maxContour)
        gradingPoints = utils.reorder(gradingPoints)

        ptOne = np.float32(maxContour)
        ptTwo = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix = cv2.getPerspectiveTransform(ptOne, ptTwo)
        imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

        ptOneGrade = np.float32(gradingPoints)
        ptTwoGrade = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])
        gradeMatrix = cv2.getPerspectiveTransform(ptOneGrade, ptTwoGrade)
        imgGradeDisplay = cv2.warpPerspective(img, gradeMatrix, (325, 150))
        # cv2.imshow("Grade", imgGradeDisplay)

        # Apply threshold
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]

        boxes = utils.splitBoxes(imgThresh)

        # Getting the non-zero pixel value of each box
        pixelVal = np.zeros((questions, choices))  # 5x5 b/c 5 questions and 5 answers
        cols = 0
        rows = 0

        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            pixelVal[rows][cols] = totalPixels
            cols += 1

            if cols == choices:
                rows += 1
                cols = 0
        print(pixelVal)

        # Finding index val of the markings
        index = []
        for x in range(0, questions):
            questionRow = pixelVal[x]
            indexVal = np.where(questionRow == np.amax(questionRow))
            index.append(indexVal[0][0])
        print(index)

        # Grading
        grading = []
        for x in range(0, questions):
            if answerKey[x] == index[x]:
                grading.append(1)
            else:
                grading.append(0)
        # print(grading)
        score = (sum(grading) / questions) * 100
        print(score)

    imgBlank = np.zeros_like(img)
    imageArray = ([img, imgGray, imgBlur, imgCanny],
                  [imgContours, imgMaxContours, imgWarpColored, imgThresh])
    imgStacked = utils.stackImages(imageArray, 0.5)

    cv2.imshow("Stacked Image ", imgStacked)

    return HttpResponse("Hello world, you're at Examinate index." + str(score))