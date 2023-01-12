import os

import numpy as np
import math
from cv2 import cv2  # TODO move this and all marking into separate script
# TODO not sure if I should do this, look for alternate
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.views.generic import TemplateView
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode

from .forms import ExamForm, QuestionForm, StudentAssessmentMarkingForm, MarkSheetForm, CsvModelForm, StudentClass, \
    StudentEditForm

from .models import Exam, Question, Csv, Student, Classroom, TeacherClass
from .models import exam
from .registration_form import RegistrationForm
from .utils import stackImages, recContour, getCornerPoints, reorder, splitBoxes, sort_contours
from collections import defaultdict
from math import floor
from django.http import HttpResponse
import csv

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

User = get_user_model()

##############
IMAGE_WIDTH = 500
IMAGE_HEIGHT = 1200
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
    0: "A",
    1: "B",
    2: "C",
    3: "D",
    4: "E"
}


##############

class Home(TemplateView):
    template_name = 'home.html'


def mark_exam(image, box_questions, questions, choices, answer_key):  # TODO handle GET requests

    print("MARKING")
    path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image))
    img = cv2.imread(path)

    # decode to read qr
    # code = decode(img)
    # print(code)
    #

    # Pre-processing
    img = cv2.resize(img, (IMAGE_WIDTH, IMAGE_HEIGHT))
    cv2.imshow("re-sized_image", img)
    imgContours = img.copy()
    imgMaxContours = img.copy()
    warped_image = img.copy()
    warped_image_threshold = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 50)  # detects edges
    # Finding all contours
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sort_contours(contours)
    draw_contours = cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)
    # Find rectangles
    recContours = recContour(contours)
    # print(getCornerPoints(maxContour))
    print("test" + str(len(recContours)))
    if len(recContours) != 0:
        # new
        #
        #     cv2.drawContours(imgMaxContours, getCornerPoints(recContours[0]), -1, (348, 0, 100), 20)
        #     cv2.drawContours(imgMaxContours, getCornerPoints(recContours[1]), -1, (200, 200, 0), 20)
        #     cv2.drawContours(imgMaxContours, getCornerPoints(recContours[2]), -1, (0, 102, 200), 20)

        total_boxes = []
        for i in range(len(recContours)):
            contour_corner_points = getCornerPoints(recContours[i])
            reordered_contour = reorder(contour_corner_points)
            recContours[i] = reordered_contour

            biggest_contour = getCornerPoints(recContours[i])
            first_point = np.float32(biggest_contour)
            second_point = np.float32([[0, 0], [IMAGE_WIDTH, 0], [0, IMAGE_HEIGHT], [IMAGE_WIDTH, IMAGE_HEIGHT]])

            matrix = cv2.getPerspectiveTransform(first_point, second_point)
            warped_image = cv2.warpPerspective(img, matrix, (IMAGE_WIDTH, IMAGE_HEIGHT))
            warped_gray_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)
            warped_image_threshold = cv2.threshold(warped_gray_image, 170, 255, cv2.THRESH_BINARY_INV)[1]

            split_boxes = splitBoxes(warped_image_threshold, box_questions.get(i), choices)
            total_boxes = total_boxes + split_boxes
        #
        pixelVal = np.zeros((questions, choices))  # 5x5 b/c 5 questions and 5 answers
        cols = 0
        rows = 0
        total_number_of_boxes = len(total_boxes)

        number_of_choices = questions * choices
        # number_of_unused_boxes = total_number_of_boxes - number_of_choices
        # print(number_of_unused_boxes)
        # total_boxes = total_boxes[:-number_of_unused_boxes]  # removes unused rows in each box

        # getting non-zero pixel values of each box
        for image in total_boxes:
            totalPixels = cv2.countNonZero(image)
            pixelVal[rows][cols] = totalPixels
            cols += 1
            if cols == choices:
                rows += 1
                cols = 0
        print(pixelVal)
        # #     # Finding index val of the markings
        index = []
        for x in range(0, questions):
            questionRow = pixelVal[x]
            indexVal = np.where(questionRow == np.amax(questionRow))
            index.append(indexVal[0][0])
        print(index)

        grading = []
        for x in range(0, questions):
            if answer_key[x] == index[x]:
                grading.append(1)
            else:
                grading.append(0)
        # print(grading)
        score = (sum(grading) / questions) * 100
        print(score)

    imgBlank = np.zeros_like(img)
    imageArray = ([img, imgGray, imgBlur, imgCanny, imgBlank],
                  [imgContours, imgMaxContours, warped_image, warped_image_threshold, imgBlank])
    imgStacked = stackImages(imageArray, 0.5)
    cv2.imshow("Stacked Image ", imgStacked)
    cv2.waitKey(0)
    return score


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
                                        key=lambda b: b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return (cnts)

class ExamListView(LoginRequiredMixin, ListView):
    model = Exam
    template_name = 'exam_list.html'
    context_object_name = 'exams'

    def get(self, request):
        form = QuestionForm()
        return render(request, 'exam_list.html', {'form': form})

    # form_class = QuestionForm


class ClassroomView(LoginRequiredMixin, ListView):
    template_name = 'classroom.html'

    def get(self, request):
        return render(request, 'classroom.html')


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

        save = page.save()
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

            mark_sheet_pk = mark_form.data["exam_assessment"]

            print("MARK SHETEt")
            print(mark_sheet_pk)

            questions = exam.MarkSheetQuestion.objects.filter(mark_sheet=mark_sheet_pk)
            mark_sheet = exam.MarkSheet.objects.filter(pk=mark_sheet_pk)

            number_of_choices = mark_sheet.values("number_of_choices").first()['number_of_choices']

            answers = questions.values_list('answer', flat=True)

            answer_key = []
            for mc in answers:
                answer_key.append(MC_DiCTIONARY.get(mc))

            saved_form = mark_form.save()

            image_file_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, saved_form.image.name))
            pages = convert_from_path(image_file_path)

            i = 0
            scores = []

            number_of_questions = len(questions)


            box_questions = get_questions_per_box(number_of_questions)
            print(answer_key)
            print(number_of_questions)
            print(box_questions)
            print(number_of_choices)

            for page in pages:
                image_file_name = 'out' + str(i) + '.jpg'
                jpeg_file_name_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, image_file_name))
                page.save(jpeg_file_name_path, 'JPEG')
                i = i + 1
                score = mark_exam(jpeg_file_name_path, box_questions, number_of_questions, number_of_choices, answer_key)
                scores.append(score)

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


def get_questions_per_box(number_of_questions):

    number_of_questions_per_box = defaultdict(int)
    number_of_sections = 0

    if number_of_questions > 20:
        for i in range(number_of_questions):
            number_of_sections = math.floor(number_of_questions / 20)

        for i in range(number_of_sections):
            number_of_questions_per_box[i] = 20

        questions = number_of_questions % 20
        if questions != 0:
            number_of_questions_per_box[len(number_of_questions_per_box)] = questions
    else:
        number_of_questions_per_box = {0 : number_of_questions}


        # if number_of_questions - i < 20:
        #     dict[z] = number_of_questions - i
        #     break
    return number_of_questions_per_box


def generate_exam_pdf(c, saved_mark_sheet_form, student, classroom):
    student_first_name = student.first_name
    student_last_name = student.last_name
    student_qr_code_path = student.qr_code.path

    student_name = student_first_name + " " + student_last_name
    x_static_position = 55
    x_position = 55
    num_of_questions = saved_mark_sheet_form.number_of_questions
    num_of_choices = saved_mark_sheet_form.number_of_choices
    subtract_to_center = 4
    y_coordinate_for_letter = 726
    y_coordinate_x = 0
    box_width = 0
    circle_y_position = 730
    new_box_position = 255
    box_x = 35
    for z in range(num_of_choices):
        box_width = box_width + 32.5
        print(box_width)
    box_dict = defaultdict(int)
    if num_of_questions <= 20:
        box_dict[0] = num_of_questions
    else:
        val_1 = num_of_questions / 20
        val_2 = num_of_questions % 20

        num_of_box = floor(val_1)

        for i in range(num_of_box):
            box_dict[i] = 20
        if val_2 > 0:
            len1 = len(box_dict)
            box_dict[len1] = val_2
    question_number_offset = 40
    question_number = 0
    c.drawInlineImage(student_qr_code_path, 520, 765, width=70, height=70)
    c.drawString(20, 820, classroom)
    c.drawString(20, 800, student_name)
    c.drawString(20, 770, "Multiple Choice")
    for i in box_dict:
        number_of_questions_per_box = box_dict.get(i)
        # print(number_of_questions_per_box

        if question_number + 1 > 99:
            question_number_offset = 45

        for y in range(number_of_questions_per_box):
            c.drawString(x_static_position - question_number_offset, y_coordinate_for_letter,
                         str(question_number + 1) + ".")
            y_coordinate_x = y_coordinate_x + 30

            for m in range(num_of_choices):
                c.drawString(x_position - subtract_to_center, y_coordinate_for_letter, MC_CAP_DICTIONARY.get(m))
                c.circle(x_position, circle_y_position, 10, stroke=1, fill=0)
                x_position = x_position + 30
            x_position = x_static_position
            circle_y_position = circle_y_position - 30
            question_number = question_number + 1
            y_coordinate_for_letter = y_coordinate_for_letter - 30

        c.rect(box_x, 750, box_width, -y_coordinate_x - 10, fill=0)
        x_static_position = new_box_position
        x_position = x_static_position
        new_box_position = new_box_position + 200
        box_x = box_x + 200
        y_coordinate_for_letter = 726
        circle_y_position = 730
        y_coordinate_x = 0

        if box_x > 400 and box_width > 131 or (box_x > 600):
            c.showPage()
            x_static_position = 55
            x_position = 55
            new_box_position = 255
            c.drawString(20, 820, classroom)
            c.drawString(20, 800, student_name)
            box_x = 35
    c.showPage()


class CreateMarkSheetView(LoginRequiredMixin, CreateView):
    context = {}

    def get(self, request):
        form = MarkSheetForm()
        form.get_teacher_class(request.user)
        self.context['form'] = form
        return render(request, 'create_marksheet.html', self.context)

    def post(self, request, *args, **kwargs):
        # TODO check if form is valids

        mark_sheet_form = MarkSheetForm(request.POST)
        mark_sheet_form.instance.user = request.user
        saved_mark_sheet_form = mark_sheet_form.save(commit=False)

        answer_key = mark_sheet_form.cleaned_data['answer_key']
        answer_key_list = answer_key.split(",")

        classroom = saved_mark_sheet_form.classroom
        students = StudentClass.objects.filter(classroom=classroom).values('student')

        student_ids = []
        for x in students:
            student_ids.append(x.get('student'))

        students = Student.objects.filter(id__in=student_ids)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
        c = canvas.Canvas(response)

        for student in students:
            generate_exam_pdf(c, saved_mark_sheet_form, student, classroom.name)

        final_pdf = c.save()
        saved_mark_sheet_form.mark_sheet_pdf = final_pdf
        os.startfile("hello.pdf")
        mark_sheet_form.save()

        for ans in answer_key_list: #TODO add validation - if the num of question in list is less than num of questions entered then add a warning.
            exam.MarkSheetQuestion.objects.create(
                mark_sheet=saved_mark_sheet_form,
                answer=ans
            )

        form = MarkSheetForm()
        self.context['form'] = form
        # return render(request, 'create_marksheet.html', self.context)
        return response


class CreateExamView(LoginRequiredMixin, CreateView):
    # model = Question
    context = {}

    def get(self, request):
        self.context['form'] = QuestionForm()
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


class EditClassView(LoginRequiredMixin, ListView):
    context = {}

    def get(self, request, **kwargs):
        self.context['form'] = StudentEditForm()
        class_list = Classroom.objects.all().filter(user=request.user)
        self.context['class_list'] = class_list
        student_class_list = StudentClass.objects.all().filter(classroom__in=class_list)
        self.context['student_class'] = student_class_list

        self.context['students'] = student_class_list.values('student')

        print(class_list)
        print(student_class_list)
        return render(request, 'view_class.html', self.context)


def selectClass(request, pk):
    print("test")
    return render(request, 'view_class.html')


class CreateClassView(LoginRequiredMixin, CreateView):
    print("test")

    def get(self, request):
        form = CsvModelForm(request.POST, request.FILES)
        return render(request, 'create_class.html', {'form': form})

    def post(self, request, **kwargs):
        form = CsvModelForm(request.POST or None, request.FILES or None)
        print("test")
        if form.is_valid():
            csv_object = form.save()
            form = CsvModelForm()
            # obj = Csv.objects.filter() #This grabs all

            class_room = Classroom
            with open(csv_object.file_name.path, 'r') as f:
                reader = csv.reader(f)

                for i, row in enumerate(reader):
                    if i == 0:
                        pass
                    else:
                        row = ",".join(row)
                        print(row)
                        # row = row.replace(",", " ")
                        row = row.split(",")
                        print(row)

                        if i == 1:
                            class_room = Classroom.objects.create(name=row[3], user=request.user)
                            TeacherClass.objects.create(
                                classroom=class_room,
                                user=request.user
                            )

                        student_first_name = row[0]
                        student_last_name = row[1]
                        student_identifier = row[2]
                        new_student = Student.objects.create(first_name=student_first_name,
                                                             last_name=student_last_name,
                                                             student_number=student_identifier)

                        StudentClass.objects.create(
                            classroom=class_room,
                            student=new_student
                        )

        return render(request, 'create_class.html', {'form': form})


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


def delete_exam(request, pk):
    if request.method == 'POST':
        exam = Exam.objects.get(pk=pk)
        exam.delete()
    return redirect('exam_list')


def delete_student(request, pk, classname):
    if request.method == 'POST':
        student = Student.objects.get(pk=pk)
        student_first_name = student.first_name
        student.delete()

        messages.success(request, "Successfully removed " + student_first_name + " from " + classname)
    return redirect('view_class')


def edit_student(request, pk, name):
    form = StudentEditForm(request.POST)
    student = form.save(commit=False)

    student_to_update = Student.objects.all().filter(id=pk)
    old_student = student_to_update

    print(old_student.values("first_name").first().get('first_name'))

    if len(student.first_name) != 0:
        old_first_name = old_student.values("first_name").first().get('first_name')
        student_to_update.update(first_name=student.first_name)
        messages.success(request,
                         "Successfully changed the first name " + old_first_name + " to " + student.first_name + " for the class " + name + ".")
    if len(student.last_name) != 0:
        old_last_name = old_student.values("last_name").first().get('last_name')
        student_to_update.update(last_name=student.last_name)
        messages.success(request,
                         "Successfully changed the last name " + old_last_name + " to " + student.last_name + " for the class " + name + ".")
    if len(student.student_number) != 0:
        old_student_number = old_student.values("student_number").first().get('student_number')
        student_to_update.update(student_number=student.student_number)
        messages.success(request,
                         "Successfully changed the student number " + old_student_number + " to " + student.student_number + " for the class " + name + ".")

    return redirect('view_class')


def delete_class(request, pk, classname):
    if request.method == 'POST':
        classroom = Classroom.objects.get(pk=pk)
        classroom.delete()

        messages.success(request, "Successfully deleted the class " + classname)
    return redirect('view_class')
