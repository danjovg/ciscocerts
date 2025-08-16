from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from .models import Student, Certification

REQ1, REQ2 = settings.REQUIRED_CERTS[:2]

class ModelLogicTests(TestCase):
    def setUp(self):
        self.s1 = Student.objects.create(full_name="Alice", email="a@example.com", slug="alice")
        self.s2 = Student.objects.create(full_name="Bob", email="b@example.com", slug="bob")

    def test_has_required_true_when_both_present(self):
        Certification.objects.create(student=self.s1, cert_type=REQ1)
        Certification.objects.create(student=self.s1, cert_type=REQ2)
        self.assertTrue(self.s1.has_required())

    def test_has_required_false_when_one_missing(self):
        Certification.objects.create(student=self.s2, cert_type=REQ1)
        self.assertFalse(self.s2.has_required())

    def test_extra_certification_classification(self):
        Certification.objects.create(student=self.s1, cert_type=REQ1)
        Certification.objects.create(student=self.s1, cert_type=REQ2)
        Certification.objects.create(student=self.s1, cert_type="Python Essentials")
        extras = [c for c in self.s1.certifications.all() if not c.is_required]
        self.assertEqual(len(extras), 1)
        self.assertEqual(extras[0].cert_type, "Python Essentials")

    def test_unique_per_student_cert_type(self):
        Certification.objects.create(student=self.s1, cert_type=REQ1)
        with self.assertRaises(Exception):
            Certification.objects.create(student=self.s1, cert_type=REQ1)

class ViewsTests(TestCase):
    def setUp(self):
        self.s = Student.objects.create(full_name="Carol", email="c@example.com", slug="carol")
        Certification.objects.create(student=self.s, cert_type=REQ1)

    def test_list_view(self):
        url = reverse("registry:student_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Carol")

    def test_detail_view(self):
        url = reverse("registry:student_detail", kwargs={"slug": "carol"})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, REQ1)
        self.assertContains(resp, REQ2)
