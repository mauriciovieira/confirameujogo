# -*- coding: utf-8 -*-
"""
    tipfyext.wtforms.form
    ~~~~~~~~~~~~~~~~~~~~~~

    Form object.

    :copyright: 2011 tipfy.org.
    :copyright: 2011 WTForms authors.
    :license: BSD, see LICENSE.txt for more details.
"""
import uuid

from wtforms import Form as BaseForm

from tipfy import Request, current_handler
from tipfyext.wtforms.fields import FileField, CsrfTokenField
from tipfyext.wtforms.validators import CsrfToken

try:
    from tipfy import i18n
except ImportError, e:
    i18n = None


class Form(BaseForm):
    csrf_protection = False
    csrf_token = CsrfTokenField()

    def __init__(self, *args, **kwargs):
        self.csrf_protection_enabled = kwargs.pop('csrf_protection',
            self.csrf_protection)

        super(Form, self).__init__(*args, **kwargs)

    def process(self, formdata=None, obj=None, **kwargs):
        """
        Take form, object data, and keyword arg input and have the fields
        process them.

        :param formdata:
            A :class:`tipfy.app.Request` object or a multidict of form data coming
            from the enduser, usually `request.form` or equivalent.
        :param obj:
            If `formdata` has no data for a field, the form will try to get it
            from the passed object.
        :param `**kwargs`:
            If neither `formdata` or `obj` contains a value for a field, the
            form will assign the value of a matching keyword argument to the
            field, if provided.
        """
        if not self.csrf_protection_enabled:
            self._fields.pop('csrf_token', None)

        if isinstance(formdata, Request):
            request = formdata
            filedata = request.files
            formdata = request.form

            if self.csrf_protection_enabled:
                kwargs['csrf_token'] = self._get_csrf_token(request)
        else:
            if self.csrf_protection_enabled:
                raise TypeError('You must pass a request object to the form '
                    'to use CSRF protection')

            filedata = None
            if formdata is not None and not hasattr(formdata, 'getlist'):
                raise TypeError("formdata should be a multidict-type wrapper "
                    "that supports the 'getlist' method")

        for name, field, in self._fields.iteritems():
            if isinstance(field, FileField):
                data = filedata
            else:
                data = formdata

            if obj is not None and hasattr(obj, name):
                field.process(data, getattr(obj, name))
            elif name in kwargs:
                field.process(data, kwargs[name])
            else:
                field.process(data)

    def _get_session(self):
        return current_handler.session_store.get_session()

    def _get_csrf_token(self, request):
        token = str(uuid.uuid4())
        token_list = self._get_session().setdefault('_csrf_token', [])
        token_list.append(token)
        # Store a maximum number of tokens.
        maximum_tokens = current_handler.get_config('tipfyext.wtforms',
            'csrf_tokens')
        while len(token_list) > maximum_tokens:
            token_list.pop(0)

        # Set the validation rule for the tokens.
        self._fields['csrf_token'].validators = [CsrfToken(token_list)]
        return token

    def _get_translations(self):
        """
        Override in subclasses to provide alternate translations factory.

        Must return an object that provides gettext() and ngettext() methods.
        """
        if i18n:
            return current_handler.i18n
        else:
            return None
