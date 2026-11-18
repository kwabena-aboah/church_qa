import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RetryQuestionViewTests(TestCase):
	def test_missing_question_returns_404(self):
		user = User.objects.create_user(username='tester', password='test-password')
		self.client.force_login(user)

		response = self.client.post(
			reverse('dashboard:retry_question', args=[uuid.uuid4()]),
			secure=True,
		)

		self.assertEqual(response.status_code, 404)
