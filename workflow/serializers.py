from rest_framework import serializers
from .models import (
    User, Course, CalendarEvent, Announcement,
    KanbanBoard, KanbanColumn, KanbanCard,
    Assignment, Submission, Timeline, TimelineEvent,
    WorkflowTemplate, WorkflowStep, WorkflowInstance,
    ReportTemplate, Report
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model"""
    full_name = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_teacher = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'full_name', 'role', 'is_admin', 'is_teacher', 'is_student',
                 'profile_picture', 'department', 'initials']
        extra_kwargs = {'password': {'write_only': True}}
        
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
        
    def get_is_admin(self, obj):
        return obj.role == 'ADMIN' if hasattr(obj, 'role') else (obj.is_staff and obj.is_superuser)
        
    def get_is_teacher(self, obj):
        return obj.role == 'TEACHER' if hasattr(obj, 'role') else (obj.is_staff and not obj.is_superuser)
        
    def get_is_student(self, obj):
        return obj.role == 'STUDENT' if hasattr(obj, 'role') else (not obj.is_staff)
        
    def get_initials(self, obj):
        full_name = obj.get_full_name().split()
        if full_name:
            return ''.join([n[0].upper() for n in full_name if n])
        return obj.username[0].upper() if obj.username else '?'
        
    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    teacher_name = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'description', 'teacher', 'teacher_name', 
                 'students', 'student_count', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name() if obj.teacher else None
    
    def get_student_count(self, obj):
        return obj.students.count()


class CalendarEventSerializer(serializers.ModelSerializer):
    """Serializer for CalendarEvent model"""
    created_by_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CalendarEvent
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 
                 'course', 'course_name', 'created_by', 'created_by_name',
                 'event_type', 'is_recurring', 'recurrence_pattern', 
                 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model"""
    author_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'course', 'course_name', 
                 'author', 'author_name', 'important', 'attachment',
                 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else None
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None


# Kanban Serializers
class KanbanCardSerializer(serializers.ModelSerializer):
    """Serializer for KanbanCard model"""
    assignees_names = serializers.SerializerMethodField()
    
    class Meta:
        model = KanbanCard
        fields = ['id', 'title', 'description', 'column', 'assignees', 
                 'assignees_names', 'due_date', 'order', 'color', 
                 'attachment', 'created_at', 'updated_at']
        
    def get_assignees_names(self, obj):
        return [user.get_full_name() for user in obj.assignees.all()]


class KanbanColumnSerializer(serializers.ModelSerializer):
    """Serializer for KanbanColumn model with nested cards"""
    cards = KanbanCardSerializer(many=True, read_only=True)
    
    class Meta:
        model = KanbanColumn
        fields = ['id', 'board', 'title', 'order', 'cards']


class KanbanBoardSerializer(serializers.ModelSerializer):
    """Serializer for KanbanBoard model with nested columns and cards"""
    columns = KanbanColumnSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KanbanBoard
        fields = ['id', 'name', 'description', 'course', 'course_name',
                 'owner', 'owner_name', 'is_template', 'columns',
                 'created_at', 'updated_at']
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() if obj.owner else None
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None


# Assignment Serializers
class SubmissionSerializer(serializers.ModelSerializer):
    """Serializer for Submission model"""
    student_name = serializers.SerializerMethodField()
    assignment_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'assignment_title', 'student', 
                 'student_name', 'submitted_at', 'files', 'comments', 
                 'score', 'feedback', 'status', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        return obj.student.get_full_name() if obj.student else None
    
    def get_assignment_title(self, obj):
        return obj.assignment.title if obj.assignment else None


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model"""
    submissions = SubmissionSerializer(many=True, read_only=True)
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'course', 'course_name',
                 'due_date', 'max_score', 'weight', 'files', 'submissions',
                 'created_at', 'updated_at']
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None


# Timeline Serializers
class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for TimelineEvent model"""
    class Meta:
        model = TimelineEvent
        fields = ['id', 'timeline', 'title', 'description', 'date', 
                 'color', 'icon', 'created_at', 'updated_at']


class TimelineSerializer(serializers.ModelSerializer):
    """Serializer for Timeline model with nested events"""
    events = TimelineEventSerializer(many=True, read_only=True)
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Timeline
        fields = ['id', 'title', 'description', 'course', 'course_name',
                 'start_date', 'end_date', 'events', 'created_at', 'updated_at']
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None


# Workflow Serializers
class WorkflowStepSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowStep model"""
    class Meta:
        model = WorkflowStep
        fields = ['id', 'template', 'name', 'description', 'order', 'duration_days']


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTemplate model with nested steps"""
    steps = WorkflowStepSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowTemplate
        fields = ['id', 'name', 'description', 'created_by', 'created_by_name',
                 'steps', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowInstance model"""
    template_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    current_step_name = serializers.SerializerMethodField()
    current_end_date = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowInstance
        fields = ['id', 'template', 'template_name', 'course', 'course_name',
                 'current_step', 'current_step_name', 'start_date', 
                 'current_end_date', 'created_at', 'updated_at']
    
    def get_template_name(self, obj):
        return obj.template.name if obj.template else None
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None
    
    def get_current_step_name(self, obj):
        return obj.current_step.name if obj.current_step else None
    
    def get_current_end_date(self, obj):
        return obj.get_current_end_date()


# Report Serializers
class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model"""
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportTemplate
        fields = ['id', 'name', 'description', 'created_by', 'created_by_name',
                 'query', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model"""
    template_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'name', 'template', 'template_name', 'created_by',
                 'created_by_name', 'course', 'course_name', 'generated_at',
                 'data', 'created_at', 'updated_at']
    
    def get_template_name(self, obj):
        return obj.template.name if obj.template else None
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
    
    def get_course_name(self, obj):
        return obj.course.name if obj.course else None
