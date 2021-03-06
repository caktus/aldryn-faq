# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django import forms

from cms.api import add_plugin
from cms.utils import permissions
from cms.utils.conf import get_cms_setting
from cms.wizards.wizard_pool import wizard_pool
from cms.wizards.wizard_base import Wizard
from cms.wizards.forms import BaseFormMixin

from parler.forms import TranslatableModelForm

from .cms_appconfig import FaqConfig
from .models import Category, Question
from .utils import is_valid_namespace


class ConfigCheckMixin(object):

    def user_has_add_permission(self, user, **kwargs):
        """
        Return True if the current user has permission to add a Category or
        Question (depending on value of `perm_string` class variable.
        :param user: The current user
        :param kwargs: Ignored here
        :return: True if user has add permission, else False
        """
        # No one can create an Article, if there is no app_config yet.
        configs = FaqConfig.objects.all()
        if not configs:
            return False
        if not any([is_valid_namespace(config.namespace)
                    for config in configs]):
            return False

        # Ensure user has permission to create articles.
        if user.is_superuser or user.has_perm(self.perm_string):
            return True

        # By default, no permission.
        return False


class FaqCategoryWizard(ConfigCheckMixin, Wizard):
    perm_string = "aldryn_faq.add_category"


class FaqQuestionWizard(ConfigCheckMixin, Wizard):
    perm_string = "aldryn_faq.add_question"

    def user_has_add_permission(self, user, **kwargs):
        """
        Return True if the current user has permission to add a Question and
        there is at least one category.
        :param user: The current user
        :param kwargs: Ignored here
        :return: True if user has add permission, else False
        """
        base_perm = super(FaqQuestionWizard, self).user_has_add_permission(
            user, **kwargs)
        return base_perm and Category.objects.exists()


class CreateFaqCategoryForm(BaseFormMixin, TranslatableModelForm):
    """
    The ModelForm for the FAQ Category wizard. Note that Category has few
    translated fields that we need to access, so, we use TranslatableModelForm
    """

    class Meta:
        model = Category
        fields = ['name', 'slug', 'appconfig']

    def __init__(self, **kwargs):
        super(CreateFaqCategoryForm, self).__init__(**kwargs)
        # TODO: FIX this nasty hack to dissallow empty app_config
        if 'appconfig' in self.fields:
            self.fields['appconfig'].required = True
        # If there's only 1 app_config, don't bother show the
        # app_config choice field, we'll choose the option for the user.
        app_configs = FaqConfig.objects.all()
        # check if app config is apphooked
        app_configs = [app_config
                       for app_config in app_configs
                       if is_valid_namespace(app_config.namespace)]
        if len(app_configs) == 1:
            self.fields['appconfig'].widget = forms.HiddenInput()
            self.fields['appconfig'].initial = app_configs[0].pk


class CreateFaqQuestionForm(BaseFormMixin, TranslatableModelForm):
    """
    The ModelForm for the FAQ Question wizard. Note that Category has few
    translated fields that we need to access, so, we use TranslatableModelForm
    """

    answer = forms.CharField(
        label="Answer", help_text=_("Optional. If provided, will be added to "
                                    "the main body of the Question answer."),
        required=False, widget=forms.Textarea())

    class Meta:
        model = Question
        fields = ['title', 'category', 'is_top', 'answer_text',
                  'answer']

    def __init__(self, **kwargs):
        super(CreateFaqQuestionForm, self).__init__(**kwargs)

        # If there's only 1 category, don't bother show the empty label (choice)
        if Category.objects.count() == 1:
            self.fields['category'].empty_label = None

    def save(self, commit=True):
        question = super(CreateFaqQuestionForm, self).save(commit=False)

        # If 'content' field has value, create a TextPlugin with same and add
        # it to the PlaceholderField
        answer = self.cleaned_data.get('answer', '')
        content_plugin = get_cms_setting('WIZARD_CONTENT_PLUGIN')
        if answer and permissions.has_plugin_permission(
                self.user, content_plugin, 'add'):

            # If the question has not been saved, then there will be no
            # Placeholder set-up for this question yet, so, ensure we have saved
            # first.
            if not question.pk:
                question.save()

            if question and question.answer:
                plugin_kwarg = {
                    'placeholder': question.answer,
                    'plugin_type': content_plugin,
                    'language': self.language_code,
                    get_cms_setting('WIZARD_CONTENT_PLUGIN_BODY'): answer,
                }
                add_plugin(**plugin_kwarg)

        if commit:
            question.save()

        return question

faq_category_wizard = FaqCategoryWizard(
    title=_(u"New FAQ category"),
    weight=400,
    form=CreateFaqCategoryForm,
    description=_(u"Create a new FAQ category.")
)

wizard_pool.register(faq_category_wizard)

faq_category_wizard = FaqQuestionWizard(
    title=_(u"New FAQ question"),
    weight=450,
    form=CreateFaqQuestionForm,
    description=_(u"Create a new FAQ question.")
)

wizard_pool.register(faq_category_wizard)
