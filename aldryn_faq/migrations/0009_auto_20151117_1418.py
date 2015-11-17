# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import app_data.fields


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_faq', '0008_generate_slugs_for_existing_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqconfig',
            name='app_data',
            field=app_data.fields.AppDataField(default='{}', editable=False),
            preserve_default=True,
        ),
    ]
