# Generated by Django 2.1.5 on 2019-03-18 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hideyhole', '0004_auto_20190318_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallpaper',
            name='image_source_sha1',
            field=models.CharField(default='sha1missing', max_length=40),
            preserve_default=False,
        ),
    ]