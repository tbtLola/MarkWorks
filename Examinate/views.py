import os

import numpy as np
from cv2 import cv2  # TODO move this and all marking into separate script
# TODO not sure if I should do this, look for alternate
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.views.generic import TemplateView
from pdf2image import convert_from_path

from .forms import ExamForm, QuestionForm, StudentAssessmentMarkingForm
from .models import Exam, Question
from .models import exam
from .registration_form import RegistrationForm
from .utils import recContour, getCornerPoints, reorder, splitBoxes

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

User = get_user_model()

##############
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 1000
NUMBER_OF_CHOICES = 5

# TODO move this into the model
MC_DiCTIONARY = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
}

MC_CAP_DICTIONARY = {
    0:"A",
    1:"B",
    2:"C",
    3:"D",
    4:"E"
}


##############

class Home(TemplateView):
    template_name = 'home.html'


def delete_exam(request, pk):
    if request.method == 'POST':
        exam = Exam.objects.get(pk=pk)
        exam.delete()
    return redirect('exam_list')


def mark_exam(image, number_of_questions, answer_key):  # TODO handle GET requests

    image_file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image))
    image = cv2.imread(image_file_path)
    resized_image = cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT))

    # # Pre-procesing
    image_contours = resized_image.copy()
    image_max_contours = resized_image.copy()
    image_gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
    image_blur = cv2.GaussianBlur(image_gray, (5, 5), 1)
    image_canny = cv2.Canny(image_blur, 10, 50)

    # Finding all contours
    contours, hierarchy = cv2.findContours(image_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sort_contours(contours)
    cv2.drawContours(image_contours, contours, -1, (0, 255, 0), 10)

    rec_contours = recContour(contours)

    if len(rec_contours) != 0:
        total_boxes = []
        for i in range(len(rec_contours)):
            contour_corner_points = getCornerPoints(rec_contours[i])
            reordered_contour = reorder(contour_corner_points)
            rec_contours[i] = reordered_contour

            first_point = np.float32(rec_contours[i])
            second_point = np.float32([[0, 0], [IMAGE_WIDTH, 0], [0, IMAGE_HEIGHT], [IMAGE_WIDTH, IMAGE_HEIGHT]])

            matrix = cv2.getPerspectiveTransform(first_point, second_point)
            warped_image = cv2.warpPerspective(resized_image, matrix, (IMAGE_WIDTH, IMAGE_HEIGHT))
            warped_gray_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
            warped_image_threshold = cv2.threshold(warped_gray_image, 170, 255, cv2.THRESH_BINARY_INV)[1]

            split_boxes = splitBoxes(warped_image_threshold)
            total_boxes = total_boxes + split_boxes
            # cv2.imshow("warpy" + str(i), warped_image)
            # cv2.imshow("gray_warpy" + str(i), warped_image)
            cv2.imshow("thres_warpy" + str(i), warped_image_threshold)

        pixelVal = np.zeros((number_of_questions, NUMBER_OF_CHOICES))  # 5x5 b/c 5 questions and 5 answers
        cols = 0
        rows = 0

        total_number_of_boxes = len(total_boxes)
        number_of_choices = number_of_questions * NUMBER_OF_CHOICES
        number_of_unused_boxes = total_number_of_boxes - number_of_choices
        total_boxes = total_boxes[:-number_of_unused_boxes]  # removes unused rows in each box

        for image in total_boxes:
            totalPixels = cv2.countNonZero(image)
            pixelVal[rows][cols] = totalPixels
            cols += 1

            if cols == NUMBER_OF_CHOICES:
                rows += 1
                cols = 0
        print(pixelVal)

        # Finding index val of the markings
        index = []
        for x in range(0, number_of_questions):
            questionRow = pixelVal[x]
            indexVal = np.where(questionRow == np.amax(questionRow))
            index.append(indexVal[0][0])
        # print(index)

        # Grading
        grading = []
        for x in range(0, number_of_questions):
            if answer_key[x] == index[x]:
                grading.append(1)
            else:
                grading.append(0)
        # print(grading)
        score = (sum(grading) / number_of_questions) * 100

        return score


def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
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
                                        key=lambda b: b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return (cnts)


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


def get_images_from_pdf(image):
    print(image)

    image_file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image))
    pages = convert_from_path(image_file_path, 500)

    i = 0
    file_name_paths = []
    for page in pages:
        image_file_name = 'out' + str(i) + '.jpg'
        print(image_file_name)

        jpeg_file_name_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image_file_name))
        print(jpeg_file_name_path)
        file_name_paths.append(jpeg_file_name_path)

        save = page.save(jpeg_file_name_path, 'JPEG')
        print(save)
        print(save.url)
        i = i + 1

    return file_name_paths


class AssessStudentExamView(LoginRequiredMixin, CreateView):
    model = exam.StudentAssessment
    form_class = StudentAssessmentMarkingForm
    success_url = reverse_lazy('exam_list')
    template_name = 'mark_exam.html'
    context = {}

    def get(self, request):
        self.context.clear()
        form = StudentAssessmentMarkingForm()
        form.getThing(request.user)  # TODO move this to an init method in the forms class
        self.context['form'] = form

        return render(request, 'mark_exam.html', self.context)

    def post(self, request, *args, **kwargs):  # TODO check if file type is pdf or jpg/png
        mark_form = StudentAssessmentMarkingForm(request.POST, request.FILES)

        if mark_form.is_valid():
            mark_form.instance.user = request.user

            exam_pk = mark_form.data["exam_assessment"]

            multiple_choice_questions = Question.objects.filter(exam_id=exam_pk).filter(question_type='MC')
            multiple_choice_answers = multiple_choice_questions.values_list('answer', flat=True)

            answer_key = []
            for mc in multiple_choice_answers:
                answer_key.append(MC_DiCTIONARY.get(mc))

            self.logTestInfo(answer_key, multiple_choice_answers, multiple_choice_questions)

            saved_form = mark_form.save()

            image_file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, saved_form.image.name))
            pages = convert_from_path(image_file_path, 500)

            i = 0
            scores = []
            for page in pages:
                image_file_name = 'out' + str(i) + '.jpg'
                jpeg_file_name_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image_file_name))
                page.save(jpeg_file_name_path, 'JPEG')
                i = i + 1
                score = mark_exam(jpeg_file_name_path, len(multiple_choice_questions), answer_key)
                scores.append(score)
                marked_student_assessment = exam.MarkedStudentAssessment(examiner_id=request.user.id,
                                                                         exam_id=exam_pk,
                                                                         grade=score,
                                                                         name="test",  # TODO update the name
                                                                         image=image_file_name)  # TODO instead of doing this maybe just use the form
                marked_student_assessment.save()

            self.context['scores'] = scores

            form = StudentAssessmentMarkingForm()
            form.getThing(request.user)  # TODO move this to an init method in the forms class
            self.context['form'] = form
        else:
            form = StudentAssessmentMarkingForm()
            form.getThing(request.user)  # TODO move this to an init method in the forms class
            self.context.clear()
            self.context['form'] = form
            return render(request, 'mark_exam.html', self.context)

        return render(request, 'mark_exam.html', self.context)

    def logTestInfo(self, answer_key, multiple_choice_answers, multiple_choice_questions):
        print("answer key: " + str(answer_key))
        print(len(multiple_choice_questions))
        print(multiple_choice_answers)


class CreateMarkSheetView(LoginRequiredMixin, CreateView):
    def get(self, request):

        num_of_questions = 1
        num_of_choices = 5

        x_position = 55
        subtract_to_center = 4
        y_coordinate_for_letter = 726
        box_width = 0

        c = canvas.Canvas("hello.pdf")

        for y in range (num_of_questions):
            c.drawString(x_position - 35, y_coordinate_for_letter, str(y + 1) + ".")
            for i in range(num_of_choices):
                c.drawString(x_position - subtract_to_center, y_coordinate_for_letter, MC_CAP_DICTIONARY.get(i))
                c.circle(x_position, 730, 10, stroke=1, fill=0)
                x_position = x_position + 30
                box_width = box_width + 32.5

        c.rect(35, 350, box_width, 400, fill=0)
        c.save()

        os.startfile("hello.pdf")

        return render(request, 'create_marksheet.html')


class CreateExamView(LoginRequiredMixin, CreateView):
    # model = Question
    context = {}

    def get(self, request):
        self.context['form'] = QuestionForm()
        self.context['exam_form'] = ExamForm()
        self.context['question'] = Question.objects.all()

        # print(request.user.id)

        form = QuestionForm()
        exam_form = ExamForm(prefix="exam")
        return render(request, 'create_exam.html', {'form': form, 'exam_form': exam_form})

    def post(self, request, *args, **kwargs):
        form = QuestionForm(request.POST)
        exam_form = ExamForm(request.POST, prefix="exam")

        if form.is_valid():
            exam = self.context['new_exam']
            exam_questions = Question.objects.filter(exam=exam)
            question_number = len(exam_questions) + 1

            form.instance.exam_assessment = exam
            question = form.save(commit=False)
            question.question_number = "Question " + str(question_number)
            question.exam = exam
            question.save()
            # question.
        if exam_form.is_valid():
            exam_form.instance.user = request.user
            new_exam = exam_form.save()
            self.context['new_exam'] = new_exam

        self.context['form'] = QuestionForm()
        self.context['exam_form'] = ExamForm()
        new_exam = self.context['new_exam']
        questions = Question.objects.filter(exam=new_exam)
        self.context['question'] = questions

        return render(request, 'create_exam.html', self.context)


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


def get_corner_points(cont):
    perimeter = cv2.arcLength(cont, True)
    approximation = cv2.approxPolyDP(cont, 0.02 * perimeter, True)
    return approximation
