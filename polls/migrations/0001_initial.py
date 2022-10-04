# Generated by Django 4.1.1 on 2022-10-01 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('examID', models.AutoField(primary_key=True, serialize=False)),
                ('examName', models.CharField(max_length=50)),
                ('examPhotoFileName', models.CharField(max_length=500)),
                ('examScore', models.IntegerField()),
            ],
        ),
    ]
