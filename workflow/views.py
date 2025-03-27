from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    User, Course, CalendarEvent, Announcement,
    KanbanBoard, KanbanColumn, KanbanCard,
    Assignment, Submission, Timeline, TimelineEvent,
    WorkflowTemplate, WorkflowStep, WorkflowInstance,
    ReportTemplate, Report, WorkflowException, InvalidWorkflowStateException
)
from .serializers import (
    UserSerializer, CourseSerializer, CalendarEventSerializer,
    AnnouncementSerializer, KanbanBoardSerializer, KanbanColumnSerializer,
    KanbanCardSerializer, AssignmentSerializer, SubmissionSerializer,
    TimelineSerializer, TimelineEventSerializer, WorkflowTemplateSerializer,
    WorkflowStepSerializer, WorkflowInstanceSerializer, ReportTemplateSerializer,
    ReportSerializer
)

# Custom permissions
class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Permission to only allow teachers and admins to access a view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_teacher or request.user.is_admin

class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admin users to access a view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_admin

class IsOwnerOrTeacherOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object, teachers, or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_admin:
            return True
        
        if request.user.is_teacher:
            # Check if the teacher is related to this object
            if hasattr(obj, 'course') and obj.course.teacher == request.user:
                return True
            if hasattr(obj, 'teacher') and obj.teacher == request.user:
                return True
        
        # Check if user is the owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
            
        return False

# User views
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_permissions(self):
        """
        Custom permissions:
        - List/Retrieve: Any authenticated user
        - Create/Update/Delete: Admin only
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Limit non-admin users to see only themselves and their related users
        """
        user = self.request.user
        if user.is_admin:
            return self.queryset
        
        if user.is_teacher:
            # Teachers can see themselves and their students
            teacher_courses = Course.objects.filter(teacher=user)
            students = User.objects.filter(enrolled_courses__in=teacher_courses)
            return User.objects.filter(Q(id=user.id) | Q(id__in=students))
        
        # Students can only see themselves and their teachers
        student_courses = user.enrolled_courses.all()
        teachers = User.objects.filter(taught_courses__in=student_courses)
        return User.objects.filter(Q(id=user.id) | Q(id__in=teachers))
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint to get current user info"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

# Course views
class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for courses
    """
    queryset = Course.objects.select_related('teacher')
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'description']
    
    def get_permissions(self):
        """
        Custom permissions:
        - List/Retrieve: Any authenticated user
        - Create/Update/Delete: Teacher or Admin only
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Filter courses based on user role:
        - Admin: All courses
        - Teacher: Their own courses
        - Student: Enrolled courses
        """
        user = self.request.user
        base_queryset = Course.objects.select_related('teacher')
        
        if user.is_admin:
            return base_queryset
        
        if user.is_teacher:
            return base_queryset.filter(teacher=user)
        
        # Student: enrolled courses
        return user.enrolled_courses.select_related('teacher').all()
    
    @action(detail=True, methods=['post'])
    def enroll_student(self, request, pk=None):
        course = self.get_object()
        
        try:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response({"detail": "Student ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            student = User.objects.get(id=student_id)
            
            if not student.is_student:
                return Response({"detail": "User is not a student"}, status=status.HTTP_400_BAD_REQUEST)
            
            course.add_student(student)
            return Response({"detail": f"Student {student.username} enrolled successfully"})
            
        except User.DoesNotExist:
            return Response({"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unenroll_student(self, request, pk=None):
        course = self.get_object()
        
        try:
            student_id = request.data.get('student_id')
            if not student_id:
                return Response({"detail": "Student ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            student = User.objects.get(id=student_id)
            course.remove_student(student)
            return Response({"detail": f"Student {student.username} unenrolled successfully"})
            
        except User.DoesNotExist:
            return Response({"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Calendar Event views
class CalendarEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for calendar events
    """
    queryset = CalendarEvent.objects.select_related('course', 'created_by')
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        """
        Filter events based on user role and optional query parameters:
        - month, year: Filter by month and year
        - course: Filter by course ID
        """
        user = self.request.user
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        course_id = self.request.query_params.get('course')
        
        # Base queryset - filter by user access
        base_queryset = CalendarEvent.objects.select_related('course', 'created_by')
        
        if user.is_admin:
            queryset = base_queryset
        elif user.is_teacher:
            # Teachers see events they created or for courses they teach
            teacher_courses = Course.objects.filter(teacher=user)
            queryset = base_queryset.filter(
                Q(created_by=user) | Q(course__in=teacher_courses)
            )
        else:
            # Students see events for courses they're enrolled in
            student_courses = user.enrolled_courses.all()
            queryset = base_queryset.filter(
                Q(course__in=student_courses)
            )
        
        # Apply additional filters
        if month and year:
            try:
                month = int(month)
                year = int(year)
                queryset = CalendarEvent.get_events_for_month(year, month, user=user)
            except (ValueError, TypeError):
                pass
        
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                queryset = queryset.filter(course=course)
            except Course.DoesNotExist:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the created_by field to current user when creating an event"""
        serializer.save(created_by=self.request.user)

# Announcement views
class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for announcements
    """
    queryset = Announcement.objects.select_related('course', 'author')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content']
    
    def get_queryset(self):
        """
        Filter announcements based on user role:
        - Admin: All announcements
        - Teacher: Announcements they authored or for courses they teach
        - Student: Announcements for courses they're enrolled in
        """
        user = self.request.user
        course_id = self.request.query_params.get('course')
        base_queryset = Announcement.objects.select_related('course', 'author')
        
        if user.is_admin:
            queryset = base_queryset
        elif user.is_teacher:
            teacher_courses = Course.objects.filter(teacher=user)
            queryset = base_queryset.filter(
                Q(author=user) | Q(course__in=teacher_courses)
            )
        else:
            student_courses = user.enrolled_courses.all()
            queryset = base_queryset.filter(course__in=student_courses)
        
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                queryset = queryset.filter(course=course)
            except Course.DoesNotExist:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the author field to current user when creating an announcement"""
        serializer.save(author=self.request.user)

# Kanban Board views
class KanbanBoardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kanban boards
    """
    queryset = KanbanBoard.objects.select_related('course', 'owner')
    serializer_class = KanbanBoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """
        Filter boards based on user role:
        - Admin: All boards
        - Teacher: Boards they own or for courses they teach
        - Student: Boards for courses they're enrolled in
        """
        user = self.request.user
        course_id = self.request.query_params.get('course')
        base_queryset = KanbanBoard.objects.select_related('course', 'owner')
        
        if user.is_admin:
            queryset = base_queryset
        elif user.is_teacher:
            teacher_courses = Course.objects.filter(teacher=user)
            queryset = base_queryset.filter(
                Q(owner=user) | Q(course__in=teacher_courses)
            )
        else:
            student_courses = user.enrolled_courses.all()
            queryset = base_queryset.filter(course__in=student_courses)
        
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                queryset = queryset.filter(course=course)
            except Course.DoesNotExist:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the owner field to current user when creating a board"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def create_default_columns(self, request, pk=None):
        """Create default columns for a Kanban board"""
        board = self.get_object()
        
        # Check if board already has columns
        if board.columns.exists():
            return Response(
                {"detail": "Board already has columns"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create default columns
        columns = [
            {"title": "To Do", "order": 0},
            {"title": "In Progress", "order": 1},
            {"title": "Done", "order": 2}
        ]
        
        for column_data in columns:
            KanbanColumn.objects.create(board=board, **column_data)
        
        serializer = self.get_serializer(board)
        return Response(serializer.data)

class KanbanColumnViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kanban columns
    """
    queryset = KanbanColumn.objects.all()
    serializer_class = KanbanColumnSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrAdmin]
    
    def get_permissions(self):
        """Use the board's permissions"""
        permission_classes = [permissions.IsAuthenticated]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes.append(IsOwnerOrTeacherOrAdmin)
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter columns by board if specified"""
        board_id = self.request.query_params.get('board')
        queryset = self.queryset
        
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        
        # Further filter based on user access to boards
        user = self.request.user
        if not user.is_admin:
            if user.is_teacher:
                teacher_courses = Course.objects.filter(teacher=user)
                accessible_boards = KanbanBoard.objects.filter(
                    Q(owner=user) | Q(course__in=teacher_courses)
                )
            else:
                student_courses = user.enrolled_courses.all()
                accessible_boards = KanbanBoard.objects.filter(course__in=student_courses)
            
            queryset = queryset.filter(board__in=accessible_boards)
        
        return queryset

class KanbanCardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kanban cards
    """
    queryset = KanbanCard.objects.all()
    serializer_class = KanbanCardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeacherOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        """Filter cards by column if specified"""
        column_id = self.request.query_params.get('column')
        queryset = self.queryset
        
        if column_id:
            queryset = queryset.filter(column_id=column_id)
        
        # Further filter based on user access to boards/columns
        user = self.request.user
        if not user.is_admin:
            if user.is_teacher:
                teacher_courses = Course.objects.filter(teacher=user)
                accessible_boards = KanbanBoard.objects.filter(
                    Q(owner=user) | Q(course__in=teacher_courses)
                )
            else:
                student_courses = user.enrolled_courses.all()
                accessible_boards = KanbanBoard.objects.filter(course__in=student_courses)
            
            accessible_columns = KanbanColumn.objects.filter(board__in=accessible_boards)
            queryset = queryset.filter(column__in=accessible_columns)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a card to a different column"""
        card = self.get_object()
        column_id = request.data.get('column_id')
        
        if not column_id:
            return Response(
                {"detail": "Column ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            column = KanbanColumn.objects.get(pk=column_id)
            # Check if user has access to both columns
            if not self.check_column_access(card.column) or not self.check_column_access(column):
                return Response(
                    {"detail": "You don't have permission to access these columns"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            card.move_to_column(column)
            serializer = self.get_serializer(card)
            return Response(serializer.data)
        
        except KanbanColumn.DoesNotExist:
            return Response(
                {"detail": "Column not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def check_column_access(self, column):
        """Check if the user has access to a column"""
        user = self.request.user
        
        if user.is_admin:
            return True
        
        if user.is_teacher:
            if column.board.owner == user:
                return True
            if column.board.course and column.board.course.teacher == user:
                return True
        
        if column.board.course and column.board.course in user.enrolled_courses.all():
            return True
        
        return False

# Frontend views
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.views.decorators.http import require_http_methods

# Frontend view functions
@require_http_methods(["GET", "POST"])
def login_view(request):
    """View for user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Get the next URL from request or default to dashboard
                next_url = request.GET.get('next', 'dashboard')
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect(next_url)
            else:
                # This shouldn't typically happen since form validation would catch it,
                # but we add it as an extra layer of security
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'workflow/login.html', {'form': form})

def logout_view(request):
    """View for user logout"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    """Dashboard view, shows different content based on user role"""
    user = request.user
    context = {}
    
    # Common data for all users
    now = timezone.now()
    one_week_later = now + timedelta(days=7)
    
    # Add recent announcements (visible to the user)
    if user.is_admin:
        recent_announcements = Announcement.objects.select_related('course', 'author').all().order_by('-created_at')[:5]
    elif user.is_teacher:
        teacher_courses = Course.objects.filter(teacher=user)
        recent_announcements = Announcement.objects.select_related('course', 'author').filter(
            Q(author=user) | Q(course__in=teacher_courses)
        ).order_by('-created_at')[:5]
    else:
        student_courses = user.enrolled_courses.all()
        recent_announcements = Announcement.objects.select_related('course', 'author').filter(
            course__in=student_courses
        ).order_by('-created_at')[:5]
    
    context['recent_announcements'] = recent_announcements
    
    # Add upcoming events (visible to the user)
    if user.is_admin:
        upcoming_events = CalendarEvent.objects.select_related('course', 'created_by').filter(
            start_date__gte=now,
            start_date__lte=one_week_later
        ).order_by('start_date')[:5]
    elif user.is_teacher:
        teacher_courses = Course.objects.filter(teacher=user)
        upcoming_events = CalendarEvent.objects.select_related('course', 'created_by').filter(
            Q(created_by=user) | Q(course__in=teacher_courses),
            start_date__gte=now,
            start_date__lte=one_week_later
        ).order_by('start_date')[:5]
    else:
        student_courses = user.enrolled_courses.all()
        upcoming_events = CalendarEvent.objects.select_related('course', 'created_by').filter(
            course__in=student_courses,
            start_date__gte=now,
            start_date__lte=one_week_later
        ).order_by('start_date')[:5]
    
    context['upcoming_events'] = upcoming_events
    
    # Role-specific data
    if user.is_admin:
        context['user_count'] = User.objects.count()
        context['course_count'] = Course.objects.count()
    elif user.is_teacher:
        teaching_courses = Course.objects.filter(teacher=user)
        context['teaching_course_count'] = teaching_courses.count()
        context['announcement_count'] = Announcement.objects.filter(
            Q(author=user) | Q(course__in=teaching_courses)
        ).count()
    else:
        enrolled_courses = user.enrolled_courses.all()
        context['enrolled_course_count'] = enrolled_courses.count()
        context['announcement_count'] = Announcement.objects.filter(
            course__in=enrolled_courses
        ).count()
    
    return render(request, 'workflow/dashboard.html', context)

@login_required
def courses(request):
    """View all courses the user has access to"""
    user = request.user
    
    if user.is_admin:
        courses = Course.objects.select_related('teacher').all()
    elif user.is_teacher:
        courses = Course.objects.select_related('teacher').filter(teacher=user)
    else:
        courses = user.enrolled_courses.select_related('teacher').all()
    
    context = {
        'courses': courses
    }
    
    return render(request, 'workflow/courses.html', context)

@login_required
def manage_courses(request):
    """View for teachers and admins to manage courses"""
    user = request.user
    
    # Only teachers and admins can access this page
    if not (user.is_teacher or user.is_admin):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    if user.is_admin:
        courses = Course.objects.select_related('teacher').all()
    else:
        courses = Course.objects.select_related('teacher').filter(teacher=user)
    
    context = {
        'courses': courses
    }
    
    return render(request, 'workflow/manage_courses.html', context)

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'workflow/profile.html')

@login_required
def calendar(request):
    """Calendar view"""
    return render(request, 'workflow/calendar.html')

@login_required
def announcements(request):
    """Announcements view"""
    return render(request, 'workflow/announcements.html')

@login_required
def kanban(request):
    """Kanban boards view"""
    return render(request, 'workflow/kanban.html')

@login_required
def reports(request):
    """Reports view for teachers"""
    if not (request.user.is_teacher or request.user.is_admin):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return render(request, 'workflow/reports.html')

@login_required
def user_management(request):
    """User management view for admins"""
    if not request.user.is_admin:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return render(request, 'workflow/user_management.html')

@login_required
def role_demo(request):
    """View to demonstrate role-based UI components"""
    return render(request, 'workflow/role_demo.html')

@login_required
def create_course(request):
    """View for creating a new course"""
    # Check if user is a teacher or admin using the role property
    if not (request.user.is_teacher or request.user.is_admin):
        messages.error(request, "You don't have permission to create courses.")
        return redirect('courses')
        
    if request.method == 'POST':
        # Process form submission
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        
        # Basic validation
        if not name or not code:
            messages.error(request, "Course name and code are required.")
            return render(request, 'workflow/create_course.html')
            
        # Check if course code already exists
        if Course.objects.filter(code=code).exists():
            messages.error(request, f"Course code '{code}' already exists. Please use a different code.")
            return render(request, 'workflow/create_course.html')
            
        # Create course
        try:
            course = Course.objects.create(
                name=name,
                code=code,
                description=description,
                teacher=request.user  # Set current user as teacher
            )
            messages.success(request, f"Course '{course.name}' created successfully!")
            return redirect('courses')
        except Exception as e:
            messages.error(request, f"Error creating course: {str(e)}")
            return render(request, 'workflow/create_course.html')
    
    # GET request - display the form
    return render(request, 'workflow/create_course.html')

@login_required
def course_students(request, pk):
    """View for managing students in a course"""
    # Get the course or return 404
    course = get_object_or_404(Course.objects.select_related('teacher'), pk=pk)
    
    # Check if user has permission to view this course's students
    if not (request.user.is_admin or (request.user.is_teacher and course.teacher == request.user)):
        messages.error(request, "You don't have permission to manage students for this course.")
        return redirect('courses')
    
    # Get all students
    if request.user.is_admin:
        # Admins can view all students
        all_students = User.objects.filter(role=User.Role.STUDENT).order_by('last_name', 'first_name')
    else:
        # Teachers can only view students in their department
        all_students = User.objects.filter(
            role=User.Role.STUDENT, 
            department=request.user.department
        ).order_by('last_name', 'first_name')
    
    # Get enrolled students
    enrolled_students = course.students.order_by('last_name', 'first_name')
    
    # Get available students (not enrolled)
    available_students = all_students.exclude(id__in=enrolled_students.values_list('id', flat=True))
    
    # Handle add/remove student actions
    if request.method == 'POST':
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        if student_id and action:
            try:
                student = get_object_or_404(User, id=student_id)
                
                if action == 'add':
                    try:
                        course.add_student(student)
                        messages.success(request, f"{student.get_full_name() or student.username} added to {course.name}.")
                    except Exception as e:
                        messages.error(request, str(e))
                
                elif action == 'remove':
                    try:
                        course.remove_student(student)
                        messages.success(request, f"{student.get_full_name() or student.username} removed from {course.name}.")
                    except Exception as e:
                        messages.error(request, str(e))
            except User.DoesNotExist:
                messages.error(request, "Student not found.")
                    
            return redirect('course_students', pk=pk)
    
    context = {
        'course': course,
        'enrolled_students': enrolled_students,
        'available_students': available_students,
    }
    
    return render(request, 'workflow/course_students.html', context)

@login_required
def course_detail(request, pk):
    """View for course details"""
    course = get_object_or_404(Course.objects.select_related('teacher'), pk=pk)
    
    # Check if the user has access to this course
    is_teacher = request.user.is_teacher and course.teacher == request.user
    is_admin = request.user.is_admin
    is_student = request.user.is_student and request.user in course.students.all()
    
    if not (is_teacher or is_admin or is_student):
        messages.error(request, "You don't have permission to view this course.")
        return redirect('courses')
    
    # Get announcements for this course
    announcements = Announcement.objects.select_related('author').filter(course=course).order_by('-created_at')[:5]
    
    # Get upcoming events for this course
    upcoming_events = CalendarEvent.objects.select_related('created_by').filter(
        course=course,
        start_date__gte=timezone.now()
    ).order_by('start_date')[:5]
    
    context = {
        'course': course,
        'announcements': announcements,
        'upcoming_events': upcoming_events,
        'is_teacher': is_teacher,
        'is_admin': is_admin,
        'is_student': is_student,
        'enrolled_students_count': course.students.count(),
    }
    
    return render(request, 'workflow/course_detail.html', context)

@login_required
def edit_course(request, pk):
    """View for editing a course"""
    course = get_object_or_404(Course.objects.select_related('teacher'), pk=pk)
    
    # Check if user has permission to edit this course
    if not (request.user.is_admin or (request.user.is_teacher and course.teacher == request.user)):
        messages.error(request, "You don't have permission to edit this course.")
        return redirect('courses')
    
    if request.method == 'POST':
        # Process form submission
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        
        # Basic validation
        if not name or not code:
            messages.error(request, "Course name and code are required.")
            return render(request, 'workflow/edit_course.html', {'course': course})
        
        # Check if course code already exists (excluding this course)
        if Course.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, f"Course code '{code}' already exists. Please use a different code.")
            return render(request, 'workflow/edit_course.html', {'course': course})
        
        # Update course
        try:
            course.name = name
            course.code = code
            course.description = description
            course.save()
            messages.success(request, f"Course '{course.name}' updated successfully!")
            return redirect('course_detail', pk=course.pk)
        except Exception as e:
            messages.error(request, f"Error updating course: {str(e)}")
            return render(request, 'workflow/edit_course.html', {'course': course})
    
    # GET request - display the form
    return render(request, 'workflow/edit_course.html', {'course': course})

@login_required
def delete_course(request, pk):
    """View for deleting a course"""
    course = get_object_or_404(Course, pk=pk)
    
    # Check if user has permission to delete this course
    if not (request.user.is_admin or (request.user.is_teacher and course.teacher == request.user)):
        messages.error(request, "You don't have permission to delete this course.")
        return redirect('courses')
    
    if request.method == 'POST':
        course_name = course.name
        try:
            course.delete()
            messages.success(request, f"Course '{course_name}' has been deleted.")
            return redirect('courses')
        except Exception as e:
            messages.error(request, f"Error deleting course: {str(e)}")
    
    # GET request - display confirmation page
    return render(request, 'workflow/delete_course.html', {'course': course})

def register_view(request):
    """View for user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'workflow/register.html', {'form': form})

@login_required
def announcement_detail(request, pk):
    """View for displaying announcement details"""
    announcement = get_object_or_404(Announcement.objects.select_related('course', 'author'), pk=pk)
    
    # Check if the user has access to this announcement
    user = request.user
    if user.is_admin:
        has_access = True
    elif user.is_teacher:
        has_access = (announcement.author == user or 
                     (announcement.course and announcement.course.teacher == user))
    else:  # Student
        has_access = announcement.course in user.enrolled_courses.all()
    
    if not has_access:
        messages.error(request, "You don't have permission to view this announcement.")
        return redirect('announcements')
    
    context = {
        'announcement': announcement,
    }
    
    return render(request, 'workflow/announcement_detail.html', context)

def frontend_view(request, path=''):
    """
    View to serve the Next.js frontend application.
    This will pass all non-API routes to the Next.js app.
    """
    return render(request, 'frontend/index.html')

from django.middleware.csrf import get_token, rotate_token
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Endpoint to get a CSRF token.
    This is helpful for frontend applications that need to make authenticated requests.
    """
    token = get_token(request)
    return JsonResponse({"csrfToken": token})

from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """API endpoint for user login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'detail': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'detail': 'This account is inactive'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        login(request, user)
        # Rotate CSRF token on login for security
        rotate_token(request)
        
        serializer = UserSerializer(user)
        return Response(serializer.data)
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # For debugging
        return Response(
            {'detail': 'An error occurred during login'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def logout_api(request):
    """API endpoint for user logout"""
    logout(request)
    return Response({'detail': 'Successfully logged out'})

@api_view(['GET'])
@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    token = get_token(request)
    return Response({'csrfToken': token})

@api_view(['GET'])
def current_user_api(request):
    """Get current user information"""
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Not authenticated'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """API endpoint for user registration"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
