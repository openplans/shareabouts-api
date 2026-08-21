import json
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from ..admin import AnonymousValuesAdmin, DataSetAdmin, PrettyAceWidget
from ..models import DataSet, AnonymousValues

User = get_user_model()


class TestAnonymousValuesAdmin(TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        AnonymousValues.objects.all().delete()

        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password'
        )
        self.owner1 = User.objects.create_user(
            username='owner1', email='owner1@example.com', password='password', is_staff=True
        )
        self.owner2 = User.objects.create_user(
            username='owner2', email='owner2@example.com', password='password', is_staff=True
        )

        self.dataset1 = DataSet.objects.create(slug='dataset-one', owner=self.owner1)
        self.dataset2 = DataSet.objects.create(slug='dataset-two', owner=self.owner2)

        self.anon1 = AnonymousValues.objects.create(
            dataset=self.dataset1,
            set_name='comments',
            data={'age': '25-34', 'race': 'Asian'}
        )
        self.anon2 = AnonymousValues.objects.create(
            dataset=self.dataset1,
            set_name='places',
            data={'location_type': 'park'}
        )
        self.anon3 = AnonymousValues.objects.create(
            dataset=self.dataset2,
            set_name='comments',
            data={'age': '35-44', 'rating': 5}
        )

        self.site = admin.AdminSite()
        self.admin = AnonymousValuesAdmin(AnonymousValues, self.site)
        self.factory = RequestFactory()

    def test_admin_registration(self):
        self.assertIn(AnonymousValues, admin.site._registry)
        self.assertIsInstance(admin.site._registry[AnonymousValues], AnonymousValuesAdmin)

    def test_list_display_columns_and_helpers(self):
        self.assertEqual(
            self.admin.list_display,
            ('id', 'owner', 'dataset', 'set_name', 'data')
        )
        self.assertEqual(self.admin.owner(self.anon1), 'owner1')
        self.assertEqual(self.admin.dataset(self.anon1), 'dataset-one')

        anon_no_ds = AnonymousValues(set_name='places', data={})
        self.assertIsNone(self.admin.owner(anon_no_ds))
        self.assertIsNone(self.admin.dataset(anon_no_ds))

    def test_list_filter_and_search_fields(self):
        self.assertIn('set_name', self.admin.list_filter)
        self.assertIn('set_name', self.admin.search_fields)
        self.assertIn('data', self.admin.search_fields)

    def test_raw_id_and_readonly_fields(self):
        self.assertEqual(self.admin.raw_id_fields, ('dataset',))
        self.assertEqual(self.admin.readonly_fields, ('id',))

    def test_get_queryset_superuser(self):
        request = self.factory.get('/admin/sa_api_v2/anonymousvalues/')
        request.user = self.superuser

        qs = self.admin.get_queryset(request)
        self.assertEqual(qs.count(), 3)
        self.assertIn(self.anon1, qs)
        self.assertIn(self.anon2, qs)
        self.assertIn(self.anon3, qs)

    def test_get_queryset_owner_scoping(self):
        request = self.factory.get('/admin/sa_api_v2/anonymousvalues/')
        request.user = self.owner1

        qs = self.admin.get_queryset(request)
        self.assertEqual(qs.count(), 2)
        self.assertIn(self.anon1, qs)
        self.assertIn(self.anon2, qs)
        self.assertNotIn(self.anon3, qs)

    def test_get_queryset_other_user(self):
        other_user = User.objects.create_user(
            username='other', email='other@example.com', password='password', is_staff=True
        )
        request = self.factory.get('/admin/sa_api_v2/anonymousvalues/')
        request.user = other_user

        qs = self.admin.get_queryset(request)
        self.assertEqual(qs.count(), 0)

    def test_get_form_with_valid_json_string(self):
        request = self.factory.get('/admin/sa_api_v2/anonymousvalues/add/')
        request.user = self.superuser

        FormClass = self.admin.get_form(request)
        form = FormClass(data={
            'dataset': self.dataset1.pk,
            'set_name': 'ballots',
            'data': '{"choices": ["A", "B"]}'
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['data'], {'choices': ['A', 'B']})

    def test_get_form_with_invalid_json_string(self):
        request = self.factory.get('/admin/sa_api_v2/anonymousvalues/add/')
        request.user = self.superuser

        FormClass = self.admin.get_form(request)
        form = FormClass(data={
            'dataset': self.dataset1.pk,
            'set_name': 'ballots',
            'data': '{"choices": [INVALID'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_pretty_ace_widget_render_dict_and_string(self):
        widget = PrettyAceWidget(mode='json')
        # String rendering
        rendered_str = widget.render('data', '{"a": 1}')
        self.assertIn('&quot;a&quot;: 1', rendered_str)

        # Dict rendering
        rendered_dict = widget.render('data', {'b': 2})
        self.assertIn('&quot;b&quot;: 2', rendered_dict)


class TestDataSetAdminAnonymousValues(TestCase):
    def setUp(self):
        User.objects.all().delete()
        DataSet.objects.all().delete()
        AnonymousValues.objects.all().delete()

        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='password'
        )
        self.dataset = DataSet.objects.create(slug='test-dataset', owner=self.superuser)

        self.site = admin.AdminSite()
        self.admin = DataSetAdmin(DataSet, self.site)

    def test_readonly_fields_includes_anonymous_values(self):
        self.assertIn('anonymous_values', self.admin.readonly_fields)

    def test_anonymous_values_link_html(self):
        html = self.admin.anonymous_values(self.dataset)
        expected_path = '/admin/sa_api_v2/anonymousvalues/?dataset=test-dataset'
        self.assertIn(f'<a href="{expected_path}">{expected_path}</a>', html)

    def test_admin_changelist_and_change_views_http(self):
        self.client.login(username='admin', password='password')

        # DataSet change view includes anonymous_values link
        response = self.client.get(f'/admin/sa_api_v2/dataset/{self.dataset.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/admin/sa_api_v2/anonymousvalues/?dataset=test-dataset')

        # AnonymousValues changelist
        AnonymousValues.objects.create(
            dataset=self.dataset,
            set_name='comments',
            data={'age': '25-34'}
        )
        response = self.client.get('/admin/sa_api_v2/anonymousvalues/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test-dataset')
        self.assertContains(response, 'comments')
