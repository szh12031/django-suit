from django.contrib.admin import ModelAdmin
from django.contrib.admin.templatetags.admin_list import result_list
from django.core.urlresolvers import reverse
from suit.templatetags.suit_list import paginator_number, paginator_info, \
    pagination, suit_list_filter_select, headers_handler, dict_to_attrs, \
    result_row_attrs, cells_handler
from suit.tests.mixins import UserTestCaseMixin, ModelsTestCaseMixin
from suit.tests.models import Book


class ModelAdminMock(object):
    def suit_row_attributes(self, obj):
        return {'class': obj.name, 'data': obj.pk}

    def suit_cell_attributes(self, obj, column):
        return {'class': 'col-' + column, 'data': obj.pk}


class ChangeListMock(object):
    list_display = ('action_checkbox', 'name', 'order', 'status')
    model_admin = ModelAdminMock()
    result_list = [Book(pk=1, name='beach'), Book(pk=2, name='sky')]


class SuitListTestCase(UserTestCaseMixin, ModelsTestCaseMixin):
    changelist = None
    book = None

    def get_changelist(self):
        self.get_response(reverse('admin:tests_book_changelist'))
        self.changelist = self.response.context_data['cl']

    def setUp(self):
        self.login_superuser()
        self.book = Book(name='Test')
        self.book.save()
        self.get_changelist()

    def test_paginator_number(self):
        output = paginator_number(self.changelist, 100)
        self.assertTrue('100' in output)

        output = paginator_number(self.changelist, '.')
        self.assertTrue('...' in output)

        output = paginator_number(self.changelist, 0)
        self.assertTrue('active' in output)

    def test_paginator_info(self):
        output = paginator_info(self.changelist)
        self.assertEqual('1 - 1', output)

    def test_pagination_one_page(self):
        pg = pagination(self.changelist)
        self.assertEqual(pg['cl'], self.changelist)
        self.assertEqual(pg['page_range'], [])
        self.assertEqual(pg['pagination_required'], False)

    def test_pagination_many_pages(self):
        per_page_original = ModelAdmin.list_per_page
        ModelAdmin.list_per_page = 20
        for x in range(25):
            book = Book(name='Test %d' % x)
            book.save()

        self.get_changelist()
        pg = pagination(self.changelist)
        ModelAdmin.list_per_page = per_page_original
        self.assertEqual(pg['cl'], self.changelist)
        self.assertEqual(len(pg['page_range']), 2)
        self.assertEqual(pg['pagination_required'], True)

    def test_suit_list_filter_select(self):
        filter_matches = (self.book.pk, self.book.name)
        self.assertEqual(len(self.changelist.filter_specs), 2)
        for i, spec in enumerate(self.changelist.filter_specs):
            filter_output = suit_list_filter_select(self.changelist, spec)
            self.assertTrue('value="%s"' % filter_matches[i] in filter_output)

    def test_suit_list_headers_handler(self):
        result_headers = [{'class_attrib': ' class="test"'}, {}]
        result = [{'class_attrib': ' class="test"'},
                  {'class_attrib': ' class="name-column "'}]
        cl = ChangeListMock()
        self.assertEqual(headers_handler(result_headers, cl), result)

    def test_suit_list_dict_to_attrs(self):
        attrs = {'class': 'test', 'data': 123}
        self.assertEqual(dict_to_attrs(attrs), ' data="123" class="test"')

    def test_suit_list_result_row_attrs(self):
        cl = ChangeListMock()
        self.assertEqual(result_row_attrs(cl, 1),
                         ' data="1" class="row1 beach"')
        self.assertEqual(result_row_attrs(cl, 2),
                         ' data="2" class="row2 sky"')

    def test_suit_list_result_row_attrs_by_response(self):
        Book.objects.all().delete()
        for x in range(2):
            book = Book(pk=x, name='sky-%s' % x)
            book.save()

        self.get_changelist()
        result = ' data="1" class="row1 suit_row_attr_class-sky-1"'
        self.assertEqual(result_row_attrs(self.changelist, 1), result)


    def test_suit_list_cells_handler(self):
        results = [
            ['<td></td>', '<th class="test"></th>',
             '<td><input class=""></td>'],
            ['<td></td>', '<th class="test"></th>',
             '<td><input class=""></td>'],
        ]
        result = [['<td data="1" class="col-action_checkbox"></td>',
                   '<td data="1" class="test"></th>',
                   '<td data="1" class="col-order"><input class=""></td>'],
                  ['<td data="2" class="col-action_checkbox"></td>',
                   '<td data="2" class="test"></th>',
                   '<td data="2" class="col-order"><input class=""></td>']]
        cl = ChangeListMock()
        self.assertEqual(cells_handler(results, cl), result)

    def test_suit_list_cells_handler_by_response(self):
        Book.objects.all().delete()
        for x in range(2):
            book = Book(pk=x, name='sky-%s' % x)
            book.save()

        self.get_changelist()
        cl = self.changelist
        results = result_list(cl)['results']
        result_cells = cells_handler(results, cl)
        self.assertTrue(
            'class="suit_cell_attr_class-id-sky-1"' in result_cells[0][1])
        self.assertTrue(' data="1"' in result_cells[0][1])
