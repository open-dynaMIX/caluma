# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-27 11:05
from __future__ import unicode_literals

from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations

import localized_fields.fields.field


class Migration(migrations.Migration):

    dependencies = [("form", "0003_auto_20180824_1334")]

    operations = [
        # needed till https://github.com/SectorLabs/django-localized-fields/pull/55
        # is merged
        HStoreExtension(),
        migrations.AlterModelOptions(
            name="formquestion", options={"ordering": ("-sort", "id")}
        ),
        migrations.AlterField(
            model_name="form",
            name="description",
            field=localized_fields.fields.field.LocalizedField(
                blank=True, null=True, required=[], uniqueness=[]
            ),
        ),
        migrations.AlterField(
            model_name="form",
            name="name",
            field=localized_fields.fields.field.LocalizedField(
                required=[], uniqueness=[]
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="label",
            field=localized_fields.fields.field.LocalizedField(
                required=[], uniqueness=[]
            ),
        ),
    ]
