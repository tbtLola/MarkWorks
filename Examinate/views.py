import os

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .registration_form import RegistrationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ExamForm, QuestionForm
from .models import Exam, Question
from cv2 import cv2  # TODO move this and all marking into separate script
# TODO not sure if I should do this, look for alternate
from django.conf import settings
from .utils import stackImages, recContour, getCornerPoints, reorder, splitBoxes

from django.contrib.auth import get_user_model
import numpy as np

User = get_user_model()

##############
IMAGE_WIDTH = 700
IMAGE_HEIGHT = 700
NUMBER_OF_QUESTIONS = 5
NUMBER_OF_CHOICES = 5
ANSWER_KEY = [1, 2, 0, 1, 4]


##############

class Home(TemplateView):
    template_name = 'home.html'


def delete_exam(request, pk):
    if request.method == 'POST':
        exam = Exam.objects.get(pk=pk)
        exam.delete()
    return redirect('exam_list')


def mark_exam(request, pk):  # TODO handle GET requests

    exam = Exam.objects.get(pk=pk)

    image_file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, exam.image.name))
    image = cv2.imread(image_file_path)
    resized_image = cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT))

    # Pre-procesing
    image_contours = resized_image.copy()
    image_max_contours = resized_image.copy()
    image_gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    image_blur = cv2.GaussianBlur(image_gray, (5, 5), 1)
    image_canny = cv2.Canny(image_blur, 10, 50)

    # Finding all contours
    contours, hierarchy = cv2.findContours(image_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(image_contours, contours, -1, (0, 255, 0), 10)

    rec_contours = rec_contour(contours)
    max_contour = get_corner_points(rec_contours[0])  # biggest contour

    grading_points = get_corner_points(rec_contours[1])

    if max_contour.size != 0 and grading_points.size != 0:
        cv2.drawContours(image_max_contours, max_contour, -1, (0, 255, 0), 20)
        cv2.drawContours(image_max_contours, grading_points, -1, (255, 0, 0), 20)

        maxContour = reorder(max_contour)
        gradingPoints = reorder(grading_points)

        ptOne = np.float32(maxContour)
        ptTwo = np.float32([[0, 0], [IMAGE_WIDTH, 0], [0, IMAGE_HEIGHT], [IMAGE_WIDTH, IMAGE_HEIGHT]])
        matrix = cv2.getPerspectiveTransform(ptOne, ptTwo)
        imgWarpColored = cv2.warpPerspective(resized_image, matrix, (IMAGE_WIDTH, IMAGE_HEIGHT))

        ptOneGrade = np.float32(gradingPoints)
        ptTwoGrade = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])
        gradeMatrix = cv2.getPerspectiveTransform(ptOneGrade, ptTwoGrade)
        imgGradeDisplay = cv2.warpPerspective(resized_image, gradeMatrix, (325, 150))
        # cv2.imshow("Grade", imgGradeDisplay)

        # Apply threshold
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]

        boxes = splitBoxes(imgThresh)

        # Getting the non-zero pixel value of each box
        pixelVal = np.zeros((NUMBER_OF_QUESTIONS, NUMBER_OF_CHOICES))  # 5x5 b/c 5 questions and 5 answers
        cols = 0
        rows = 0

        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            pixelVal[rows][cols] = totalPixels
            cols += 1

            if cols == NUMBER_OF_CHOICES:
                rows += 1
                cols = 0
        print(pixelVal)

        # Finding index val of the markings
        index = []
        for x in range(0, NUMBER_OF_QUESTIONS):
            questionRow = pixelVal[x]
            indexVal = np.where(questionRow == np.amax(questionRow))
            index.append(indexVal[0][0])
        print(index)

        # Grading
        grading = []
        for x in range(0, NUMBER_OF_QUESTIONS):
            if ANSWER_KEY[x] == index[x]:
                grading.append(1)
            else:
                grading.append(0)
        # print(grading)
        score = (sum(grading) / NUMBER_OF_QUESTIONS) * 100
        print(score)

        Exam.objects.filter(pk=pk).update(grade=score)

    return redirect('exam_list')


class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam_list.html'
    context_object_name = 'exams'
    # form_class = QuestionForm

    def get(self, request):
        form = QuestionForm()
        return render(request, 'exam_list.html', {'form': form})


class AddQuestionView(ListView):
    model = Question

    def get(self, request):
        form = QuestionForm()
        return render(request, 'add_question.html', {'form': form})


class UploadExamView(LoginRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    success_url = reverse_lazy('exam_list')
    template_name = 'upload_exam.html'

class CreateExamView(LoginRequiredMixin, CreateView):
    model = Question

    def get(self, request):
        form = QuestionForm()
        return render(request, 'create_exam.html', {'form':form})


def signup(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'registration/signup.html', {
        'form': form
    })


def rec_contour(contours):
    rec_con = []

    for i in contours:
        area = cv2.contourArea(i)
        # print("Area: ", area)
        if area > 50:
            perimeter = cv2.arcLength(i, True)
            approximation = cv2.approxPolyDP(i, 0.02 * perimeter, True)
            # print("Corner Points", len(approximation)) #The ones with 4 are essentially a square or rectangle
            if len(approximation) == 4:
                rec_con.append(i)
    rec_con = sorted(rec_con, key=cv2.contourArea, reverse=True)
    return rec_con


def get_corner_points(cont):
    perimeter = cv2.arcLength(cont, True)
    approximation = cv2.approxPolyDP(cont, 0.02 * perimeter, True)
    return approximation
