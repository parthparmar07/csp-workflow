from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from django.utils.translation import gettext_lazy as _

# Custom Exceptions
class WorkflowException(Exception):
    """Base exception for workflow related errors"""
    pass

class PermissionDeniedException(WorkflowException):
    """Raised when a user does not have permission to perform an action"""
    pass

class InvalidWorkflowStateException(WorkflowException):
    """Raised when trying to transition to an invalid workflow state"""
    pass

class DueDatePassedException(WorkflowException):
    """Raised when an action is attempted after due date"""
    pass

# User Model
class User(AbstractUser):
    """Custom user model for the university workflow system"""
    
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('Student')
        TEACHER = 'TEACHER', _('Teacher')
        ADMIN = 'ADMIN', _('Admin')
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @classmethod
    def get_teachers(cls):
        """Get all teacher users"""
        return cls.objects.filter(role=cls.Role.TEACHER)
    
    def can_manage_course(self, course):
        """Check if user can manage a course"""
        if self.is_admin:
            return True
        if self.is_teacher and course.teacher == self:
            return True
        return False
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

# Course Model
class Course(models.Model):
    """Course model for university classes"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses',
                               limit_choices_to={'role': User.Role.TEACHER})
    students = models.ManyToManyField(User, related_name='enrolled_courses', 
                                    limit_choices_to={'role': User.Role.STUDENT}, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def add_student(self, student):
        """Add a student to the course"""
        if not student.is_student:
            raise ValidationError("Only users with student role can be added to courses")
        self.students.add(student)
        
    def remove_student(self, student):
        """Remove a student from the course"""
        self.students.remove(student)
    
    def __str__(self):
        return f"{self.code}: {self.name}"

# Abstract Base Model
class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Calendar Event Model
class CalendarEvent(BaseModel):
    """Calendar event model for scheduling"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    
    class EventType(models.TextChoices):
        CLASS = 'CLASS', _('Class')
        ASSIGNMENT = 'ASSIGNMENT', _('Assignment')
        EXAM = 'EXAM', _('Exam')
        OTHER = 'OTHER', _('Other')
    
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.OTHER)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)
    
    def clean(self):
        """Validate the event dates"""
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def get_events_for_month(year, month, user=None, course=None):
        """Get events for a specific month, optionally filtered by user or course"""
        # Validate input parameters
        try:
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
                
            start_date = timezone.datetime(year, month, 1)
            # Calculate end date (first day of next month)
            if month == 12:
                end_date = timezone.datetime(year + 1, 1, 1)
            else:
                end_date = timezone.datetime(year, month + 1, 1)
            
            events = CalendarEvent.objects.filter(
                start_date__gte=start_date,
                start_date__lt=end_date
            )
            
            if user:
                # Filter by events created by user or for courses they're involved with
                user_courses = []
                if hasattr(user, 'is_student') and user.is_student:
                    user_courses = user.enrolled_courses.all()
                elif hasattr(user, 'is_teacher') and user.is_teacher:
                    user_courses = user.taught_courses.all()
                
                events = events.filter(
                    models.Q(created_by=user) | 
                    models.Q(course__in=user_courses)
                )
            
            if course:
                events = events.filter(course=course)
                
            return events
        except (ValueError, TypeError) as e:
            # Log the error and return an empty queryset
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_events_for_month: {str(e)}")
            return CalendarEvent.objects.none()
    
    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%Y-%m-%d %H:%M')})"

# Announcement Model
class Announcement(BaseModel):
    """Announcement model for course communications"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    important = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    def clean(self):
        """Validate announcement data"""
        if len(self.title) < 5:
            raise ValidationError("Title must be at least 5 characters long")
        if len(self.content) < 10:
            raise ValidationError("Content must be at least 10 characters long")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.course.code}"

# Kanban Board Models
class KanbanBoard(BaseModel):
    """Kanban board model for task management"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='boards', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    is_template = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class KanbanColumn(models.Model):
    """Columns for Kanban boards (e.g., To Do, In Progress, Done)"""
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} - {self.board.name}"

class KanbanCard(BaseModel):
    """Cards for Kanban columns representing tasks"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    column = models.ForeignKey(KanbanColumn, on_delete=models.CASCADE, related_name='cards')
    assignees = models.ManyToManyField(User, related_name='assigned_cards', blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=20, default="white")
    attachment = models.FileField(upload_to='kanban_attachments/', null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def move_to_column(self, column):
        """Move card to a different column"""
        from django.db import transaction
        
        with transaction.atomic():
            old_column = self.column
            self.column = column
            self.save()
            
            # Log the movement (for demonstration of OOP concepts)
            try:
                from django.utils import timezone
                self.description += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Moved from '{old_column.title}' to '{column.title}'"
                self.save(update_fields=['description'])
            except Exception:
                # Don't let logging failure stop the move operation
                pass
    
    def __str__(self):
        return self.title

# Assignment Model
class Assignment(BaseModel):
    """Assignment model for course assignments"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField()
    max_score = models.PositiveIntegerField(default=100)
    weight = models.PositiveIntegerField(default=1, help_text="Weight of this assignment in the final grade")
    files = models.FileField(upload_to='assignments/', null=True, blank=True)
    
    def is_past_due(self):
        """Check if the assignment is past its due date"""
        return timezone.now() > self.due_date
    
    def __str__(self):
        return f"{self.title} - {self.course.code} (Due: {self.due_date.strftime('%Y-%m-%d %H:%M')})"

class Submission(BaseModel):
    """Student submission for an assignment"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions',
                               limit_choices_to={'role': User.Role.STUDENT})
    submitted_at = models.DateTimeField(auto_now_add=True)
    files = models.FileField(upload_to='submissions/')
    comments = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        SUBMITTED = 'SUBMITTED', _('Submitted')
        GRADED = 'GRADED', _('Graded')
        RETURNED = 'RETURNED', _('Returned')
    
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    
    def is_late(self):
        """Check if submission was submitted after the due date"""
        return self.submitted_at > self.assignment.due_date
    
    def submit(self):
        """Submit the assignment"""
        if self.status == self.Status.DRAFT:
            self.status = self.Status.SUBMITTED
            self.save()
        else:
            raise InvalidWorkflowStateException("Only drafts can be submitted")
    
    def grade(self, score, feedback=""):
        """Grade the submission"""
        if self.status != self.Status.SUBMITTED:
            raise InvalidWorkflowStateException("Only submitted assignments can be graded")
        self.score = score
        self.feedback = feedback
        self.status = self.Status.GRADED
        self.save()
    
    def return_to_student(self):
        """Return the graded submission to the student"""
        if self.status != self.Status.GRADED:
            raise InvalidWorkflowStateException("Only graded assignments can be returned")
        self.status = self.Status.RETURNED
        self.save()
    
    def __str__(self):
        return f"{self.student.username}'s submission for {self.assignment.title}"

# Timeline Model
class Timeline(BaseModel):
    """Timeline model for tracking project progress"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='timelines')
    start_date = models.DateField()
    end_date = models.DateField()
    
    def clean(self):
        """Validate timeline dates"""
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"

class TimelineEvent(BaseModel):
    """Individual events within a timeline"""
    timeline = models.ForeignKey(Timeline, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    color = models.CharField(max_length=20, default="blue")
    icon = models.CharField(max_length=50, blank=True)
    
    def clean(self):
        """Validate the event is within the timeline bounds"""
        if self.date < self.timeline.start_date or self.date > self.timeline.end_date:
            raise ValidationError("Event date must be within timeline start and end dates")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.date}"

# Workflow Models
class WorkflowTemplate(BaseModel):
    """Template for workflows that can be applied to courses"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workflows')
    
    @classmethod
    def get_available_templates(cls, user):
        """Get workflow templates available to a user based on their role"""
        if user.is_admin:
            return cls.objects.all()
        return cls.objects.filter(created_by=user)
    
    def __str__(self):
        return self.name

class WorkflowStep(models.Model):
    """Individual step in a workflow template"""
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    duration_days = models.PositiveIntegerField(default=7)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} (Step {self.order} in {self.template.name})"

class WorkflowInstance(BaseModel):
    """Instance of a workflow applied to a course"""
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='instances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='workflows')
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    
    def advance_step(self):
        """Move workflow to the next step"""
        from django.db import transaction
        
        with transaction.atomic():
            if not self.current_step:
                # Initialize with first step
                try:
                    self.current_step = self.template.steps.order_by('order').first()
                    self.save()
                    return True
                except WorkflowStep.DoesNotExist:
                    raise InvalidWorkflowStateException("No steps defined in this workflow")
            else:
                # Move to next step
                try:
                    next_step = self.template.steps.filter(order__gt=self.current_step.order).order_by('order').first()
                    if next_step:
                        self.current_step = next_step
                        self.save()
                        return True
                    else:
                        # Workflow completed
                        self.current_step = None
                        self.save()
                        return False
                except WorkflowStep.DoesNotExist:
                    raise InvalidWorkflowStateException("No next step available")
    
    def get_current_end_date(self):
        """Calculate the end date for the current step"""
        if not self.current_step:
            return None
        import datetime
        return self.start_date + datetime.timedelta(days=self.current_step.duration_days)
    
    def __str__(self):
        return f"{self.template.name} for {self.course.code}"

# Report Models
class ReportTemplate(BaseModel):
    """Template for generating reports"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_templates')
    query = models.TextField(help_text="SQL or JSONPath query to generate report data")
    
    def __str__(self):
        return self.name

class Report(BaseModel):
    """Generated report instance"""
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='reports')
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)
    
    def regenerate(self):
        """Regenerate the report data"""
        # This would execute the template query and update the data
        # Implementation would depend on the specific querying mechanism
        self.generated_at = timezone.now()
        self.save()
    
    def __str__(self):
        return self.name
