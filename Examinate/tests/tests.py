import unittest
from Examinate import views


class TestAssessStudentExamView(unittest.TestCase):

    def test_20_questions(self):
        number_of_questions_per_box = {0:20, 1:20}
        self.assertEqual(number_of_questions_per_box, views.get_questions_per_box(40))

    def test_22_questions(self):
        number_of_questions_per_box = {0:20, 1:2}
        self.assertEqual(number_of_questions_per_box, views.get_questions_per_box(22))

    def test_19_questions(self):
        number_of_questions_per_box = {0:19}
        self.assertEqual(number_of_questions_per_box, views.get_questions_per_box(19))

    def test_42_questions(self):
        number_of_questions_per_box = {0:20, 1:20, 2:2}
        self.assertEqual(number_of_questions_per_box, views.get_questions_per_box(42))

    def test_60_questions(self):
        number_of_questions_per_box = {0:20, 1:20, 2:20}
        self.assertEqual(number_of_questions_per_box, views.get_questions_per_box(60))


