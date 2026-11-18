from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class WhatsAppWebhookTests(TestCase):
	def test_verification_token_is_not_written_to_logs(self):
		token = settings.WHATSAPP_VERIFY_TOKEN

		with self.assertLogs('sermons.views', level='INFO') as captured:
			response = self.client.get(
				reverse('whatsapp_webhook'),
				{
					'hub.mode': 'subscribe',
					'hub.verify_token': token,
					'hub.challenge': 'challenge-value',
				},
				secure=True,
			)

		self.assertEqual(response.status_code, 200)
		self.assertNotIn(token, '\n'.join(captured.output))
