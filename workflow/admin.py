from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Course, CalendarEvent, Announcement, KanbanBoard, 
    KanbanColumn, KanbanCard, Assignment, Submission, 
    Timeline, TimelineEvent, WorkflowTemplate, WorkflowStep, 
    WorkflowInstance, ReportTemplate, Report
)

# User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'profile_picture', 'department')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('role', 'profile_picture', 'department')}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'teacher', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'description')
    filter_horizontal = ('students',)

# Calendar Event Admin
@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'course', 'created_by')
    list_filter = ('event_type', 'start_date', 'is_recurring')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'

# Announcement Admin
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'important', 'created_at')
    list_filter = ('important', 'created_at', 'course')
    search_fields = ('title', 'content')

# Kanban Board Admin
@admin.register(KanbanBoard)
class KanbanBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'owner', 'is_template')
    list_filter = ('is_template', 'created_at')
    search_fields = ('name', 'description')

@admin.register(KanbanColumn)
class KanbanColumnAdmin(admin.ModelAdmin):
    list_display = ('title', 'board', 'order')
    list_filter = ('board',)
    search_fields = ('title',)
    ordering = ('order',)

@admin.register(KanbanCard)
class KanbanCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'column', 'due_date', 'order')
    list_filter = ('column__board', 'due_date')
    search_fields = ('title', 'description')
    filter_horizontal = ('assignees',)

# Assignment Admin
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'max_score')
    list_filter = ('course', 'due_date')
    search_fields = ('title', 'description')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'status', 'score')
    list_filter = ('status', 'submitted_at', 'assignment')
    search_fields = ('student__username', 'assignment__title', 'comments', 'feedback')
    readonly_fields = ('submitted_at',)

# Timeline Admin
@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_date', 'end_date')
    list_filter = ('course', 'start_date')
    search_fields = ('title', 'description')

@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'timeline', 'date')
    list_filter = ('timeline', 'date')
    search_fields = ('title', 'description')

# Workflow Admin
@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')

@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'order', 'duration_days')
    list_filter = ('template',)
    search_fields = ('name', 'description')
    ordering = ('template', 'order')

@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ('template', 'course', 'current_step', 'start_date')
    list_filter = ('template', 'course', 'start_date')
    search_fields = ('template__name', 'course__name')

# Report Admin
@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'query')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'course', 'created_by', 'generated_at')
    list_filter = ('template', 'course', 'generated_at')
    search_fields = ('name', 'template__name')
    readonly_fields = ('generated_at',)
