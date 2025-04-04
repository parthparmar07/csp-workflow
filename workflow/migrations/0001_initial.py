# Generated by Django 5.1.7 on 2025-03-24 13:47

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('STUDENT', 'Student'), ('TEACHER', 'Teacher'), ('ADMIN', 'Admin')], default='STUDENT', max_length=10)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('department', models.CharField(blank=True, max_length=100)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('students', models.ManyToManyField(blank=True, limit_choices_to={'role': 'STUDENT'}, related_name='enrolled_courses', to=settings.AUTH_USER_MODEL)),
                ('teacher', models.ForeignKey(limit_choices_to={'role': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='taught_courses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('event_type', models.CharField(choices=[('CLASS', 'Class'), ('ASSIGNMENT', 'Assignment'), ('EXAM', 'Exam'), ('OTHER', 'Other')], default='OTHER', max_length=20)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurrence_pattern', models.CharField(blank=True, max_length=50)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='workflow.course')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('due_date', models.DateTimeField()),
                ('max_score', models.PositiveIntegerField(default=100)),
                ('weight', models.PositiveIntegerField(default=1, help_text='Weight of this assignment in the final grade')),
                ('files', models.FileField(blank=True, null=True, upload_to='assignments/')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='workflow.course')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('important', models.BooleanField(default=False)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='announcements/')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to=settings.AUTH_USER_MODEL)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='workflow.course')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KanbanBoard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_template', models.BooleanField(default=False)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boards', to='workflow.course')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KanbanColumn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='workflow.kanbanboard')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='KanbanCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('color', models.CharField(default='white', max_length=20)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='kanban_attachments/')),
                ('assignees', models.ManyToManyField(blank=True, related_name='assigned_cards', to=settings.AUTH_USER_MODEL)),
                ('column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='workflow.kanbancolumn')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ReportTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('query', models.TextField(help_text='SQL or JSONPath query to generate report data')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('data', models.JSONField(default=dict)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='workflow.course')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_reports', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='workflow.reporttemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('files', models.FileField(upload_to='submissions/')),
                ('comments', models.TextField(blank=True)),
                ('score', models.FloatField(blank=True, null=True)),
                ('feedback', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('SUBMITTED', 'Submitted'), ('GRADED', 'Graded'), ('RETURNED', 'Returned')], default='DRAFT', max_length=10)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='workflow.assignment')),
                ('student', models.ForeignKey(limit_choices_to={'role': 'STUDENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timelines', to='workflow.course')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TimelineEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('date', models.DateField()),
                ('color', models.CharField(default='blue', max_length=20)),
                ('icon', models.CharField(blank=True, max_length=50)),
                ('timeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='workflow.timeline')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_workflows', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkflowStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('duration_days', models.PositiveIntegerField(default=7)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='workflow.workflowtemplate')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to='workflow.course')),
                ('current_step', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='workflow.workflowstep')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='workflow.workflowtemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
