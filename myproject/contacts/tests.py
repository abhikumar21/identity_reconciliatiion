from django.test import TestCase
from rest_framework.test import APIClient
from .models import Contact


class IdentifyContactTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_first_contact(self):
        response = self.client.post('/identify/', {
            'email': 'a@example.com',
            'phoneNumber': '111111'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.data['contact']
        self.assertListEqual(sorted(data['emails']), ['a@example.com'])
        self.assertListEqual(sorted(data['phoneNumbers']), ['111111'])

    def test_link_email_to_existing_phone(self):
        self.client.post('/identify/', {'phoneNumber': '222222'}, format='json')
        response = self.client.post('/identify/', {
            'email': 'b@example.com',
            'phoneNumber': '222222'
        }, format='json')
        data = response.data['contact']
        self.assertIn('b@example.com', data['emails'])
        self.assertIn('222222', data['phoneNumbers'])
        self.assertGreaterEqual(len(data['secondaryContactIds']), 1)

    def test_link_phone_to_existing_email(self):
        self.client.post('/identify/', {'email': 'c@example.com'}, format='json')
        response = self.client.post('/identify/', {
            'email': 'c@example.com',
            'phoneNumber': '333333'
        }, format='json')
        data = response.data['contact']
        self.assertIn('c@example.com', data['emails'])
        self.assertIn('333333', data['phoneNumbers'])

    def test_merge_multiple_emails_and_phones(self):
        self.client.post('/identify/', {'email': 'd@example.com', 'phoneNumber': '444444'}, format='json')
        self.client.post('/identify/', {'email': 'e@example.com', 'phoneNumber': '444444'}, format='json')
        self.client.post('/identify/', {'email': 'e@example.com', 'phoneNumber': '555555'}, format='json')

        response = self.client.post('/identify/', {'email': 'f@example.com', 'phoneNumber': '555555'}, format='json')
        data = response.data['contact']
        self.assertEqual(sorted(data['emails']), ['d@example.com', 'e@example.com', 'f@example.com'])
        self.assertEqual(sorted(data['phoneNumbers']), ['444444', '555555'])
        self.assertEqual(len(data['secondaryContactIds']), 3)

    def test_only_phone_then_email(self):
        self.client.post('/identify/', {'phoneNumber': '666666'}, format='json')
        response = self.client.post('/identify/', {'email': 'g@example.com', 'phoneNumber': '666666'}, format='json')
        data = response.data['contact']
        self.assertIn('g@example.com', data['emails'])
        self.assertIn('666666', data['phoneNumbers'])

    def test_only_email_then_phone(self):
        self.client.post('/identify/', {'email': 'h@example.com'}, format='json')
        response = self.client.post('/identify/', {'email': 'h@example.com', 'phoneNumber': '777777'}, format='json')
        data = response.data['contact']
        self.assertIn('h@example.com', data['emails'])
        self.assertIn('777777', data['phoneNumbers'])

    def test_transitive_merge_across_multiple_contacts(self):
        self.client.post('/identify/', {'email': 'i1@example.com', 'phoneNumber': '888888'}, format='json')
        self.client.post('/identify/', {'email': 'i2@example.com', 'phoneNumber': '999999'}, format='json')
        self.client.post('/identify/', {'email': 'i1@example.com', 'phoneNumber': '999999'}, format='json')
        response = self.client.post('/identify/', {'email': 'i3@example.com', 'phoneNumber': '888888'}, format='json')
        data = response.data['contact']
        self.assertEqual(sorted(data['emails']), ['i1@example.com', 'i2@example.com', 'i3@example.com'])
        self.assertEqual(sorted(data['phoneNumbers']), ['888888', '999999'])
        self.assertEqual(len(data['secondaryContactIds']), 2)

    def test_duplicate_submission(self):
        self.client.post('/identify/', {'email': 'j@example.com', 'phoneNumber': '101010'}, format='json')
        response = self.client.post('/identify/', {'email': 'j@example.com', 'phoneNumber': '101010'}, format='json')
        self.assertEqual(len(Contact.objects.all()), 1)

    def test_only_email(self):
        response = self.client.post('/identify/', {'email': 'k@example.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('k@example.com', response.data['contact']['emails'])

    def test_only_phone(self):
        response = self.client.post('/identify/', {'phoneNumber': '111999'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('111999', response.data['contact']['phoneNumbers'])

    def test_error_on_empty_input(self):
        response = self.client.post('/identify/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
