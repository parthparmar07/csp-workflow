from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from workflow.models import Course, Announcement, CalendarEvent
from django.db import transaction
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates demo data to demonstrate role-based permissions'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating demo data...')
        
        with transaction.atomic():
            # Create users with different roles
            self.create_users()
            
            # Create courses
            self.create_courses()
            
            # Create announcements
            self.create_announcements()
            
            # Create calendar events
            self.create_calendar_events()
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.print_login_credentials()
    
    def create_users(self):
        self.stdout.write('Creating users...')
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@university.edu',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin1234')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.username}')
        
        # Create teacher users
        teachers_data = [
            {
                'username': 'teacher1',
                'email': 'teacher1@university.edu',
                'first_name': 'Robert',
                'last_name': 'Smith',
                'department': 'Computer Science',
                'password': 'teacher1234'
            },
            {
                'username': 'teacher2',
                'email': 'teacher2@university.edu',
                'first_name': 'Emily',
                'last_name': 'Johnson',
                'department': 'Mathematics',
                'password': 'teacher1234'
            },
        ]
        
        self.teachers = []
        for data in teachers_data:
            password = data.pop('password')
            teacher, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'role': User.Role.TEACHER,
                    'is_staff': True,
                }
            )
            if created:
                teacher.set_password(password)
                teacher.save()
                self.stdout.write(f'Created teacher user: {teacher.username}')
            self.teachers.append(teacher)
        
        # Create student users
        students_data = [
            {
                'username': 'student1',
                'email': 'student1@university.edu',
                'first_name': 'Michael',
                'last_name': 'Brown',
                'department': 'Computer Science',
                'password': 'student1234'
            },
            {
                'username': 'student2',
                'email': 'student2@university.edu',
                'first_name': 'Sophia',
                'last_name': 'Lee',
                'department': 'Computer Science',
                'password': 'student1234'
            },
            {
                'username': 'student3',
                'email': 'student3@university.edu',
                'first_name': 'James',
                'last_name': 'Wilson',
                'department': 'Mathematics',
                'password': 'student1234'
            },
        ]
        
        self.students = []
        for data in students_data:
            password = data.pop('password')
            student, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'role': User.Role.STUDENT,
                }
            )
            if created:
                student.set_password(password)
                student.save()
                self.stdout.write(f'Created student user: {student.username}')
            self.students.append(student)
    
    def create_courses(self):
        self.stdout.write('Creating courses...')
        
        # Create courses
        courses_data = [
            {
                'name': 'Introduction to Programming',
                'code': 'CS101',
                'description': 'A beginner-friendly introduction to programming concepts using Python.',
                'teacher': self.teachers[0],
            },
            {
                'name': 'Advanced Programming',
                'code': 'CS201',
                'description': 'Advanced programming concepts including data structures and algorithms.',
                'teacher': self.teachers[0],
            },
            {
                'name': 'Calculus I',
                'code': 'MATH101',
                'description': 'Introduction to differential and integral calculus.',
                'teacher': self.teachers[1],
            },
        ]
        
        self.courses = []
        for data in courses_data:
            course, created = Course.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'teacher': data['teacher'],
                }
            )
            if created:
                self.stdout.write(f'Created course: {course.name}')
            
            # Enroll students
            if course.code == 'CS101':
                # Enroll all students in Intro to Programming
                for student in self.students:
                    try:
                        course.add_student(student)
                        self.stdout.write(f'Enrolled {student.username} in {course.name}')
                    except Exception as e:
                        self.stdout.write(f'Failed to enroll {student.username}: {str(e)}')
            
            elif course.code == 'CS201':
                # Enroll only CS students in Advanced Programming
                for student in self.students:
                    if student.department == 'Computer Science':
                        try:
                            course.add_student(student)
                            self.stdout.write(f'Enrolled {student.username} in {course.name}')
                        except Exception as e:
                            self.stdout.write(f'Failed to enroll {student.username}: {str(e)}')
            
            elif course.code == 'MATH101':
                # Enroll math student in Calculus
                for student in self.students:
                    if student.department == 'Mathematics':
                        try:
                            course.add_student(student)
                            self.stdout.write(f'Enrolled {student.username} in {course.name}')
                        except Exception as e:
                            self.stdout.write(f'Failed to enroll {student.username}: {str(e)}')
            
            self.courses.append(course)
    
    def create_announcements(self):
        self.stdout.write('Creating announcements...')
        
        announcements_data = [
            {
                'title': 'Welcome to Introduction to Programming',
                'content': 'Welcome to CS101! In this course, we will learn the fundamentals of programming using Python. Please make sure to complete the pre-course survey by the end of this week.',
                'course': self.courses[0],
                'author': self.teachers[0],
                'important': True,
            },
            {
                'title': 'First Assignment Posted',
                'content': 'The first assignment has been posted. Please complete it by next Friday.',
                'course': self.courses[0],
                'author': self.teachers[0],
                'important': False,
            },
            {
                'title': 'Welcome to Advanced Programming',
                'content': 'Welcome to CS201! This course builds on the concepts from CS101. We will be diving deeper into algorithms and data structures.',
                'course': self.courses[1],
                'author': self.teachers[0],
                'important': True,
            },
            {
                'title': 'Welcome to Calculus I',
                'content': 'Welcome to MATH101! This course will introduce you to the concepts of calculus, including limits, derivatives, and integrals.',
                'course': self.courses[2],
                'author': self.teachers[1],
                'important': True,
            },
        ]
        
        for data in announcements_data:
            announcement, created = Announcement.objects.get_or_create(
                title=data['title'],
                course=data['course'],
                defaults={
                    'content': data['content'],
                    'author': data['author'],
                    'important': data['important'],
                }
            )
            if created:
                self.stdout.write(f'Created announcement: {announcement.title}')
    
    def create_calendar_events(self):
        self.stdout.write('Creating calendar events...')
        
        now = timezone.now()
        
        events_data = [
            {
                'title': 'Introduction to Programming - Lecture 1',
                'description': 'First lecture of the semester. Introduction to Python.',
                'start_date': now + timedelta(days=1, hours=10),
                'end_date': now + timedelta(days=1, hours=12),
                'course': self.courses[0],
                'created_by': self.teachers[0],
                'event_type': CalendarEvent.EventType.CLASS,
            },
            {
                'title': 'Introduction to Programming - Assignment Due',
                'description': 'First assignment due date.',
                'start_date': now + timedelta(days=7, hours=23, minutes=59),
                'end_date': now + timedelta(days=7, hours=23, minutes=59),
                'course': self.courses[0],
                'created_by': self.teachers[0],
                'event_type': CalendarEvent.EventType.ASSIGNMENT,
            },
            {
                'title': 'Advanced Programming - Lecture 1',
                'description': 'First lecture of the semester. Review of Python basics.',
                'start_date': now + timedelta(days=2, hours=14),
                'end_date': now + timedelta(days=2, hours=16),
                'course': self.courses[1],
                'created_by': self.teachers[0],
                'event_type': CalendarEvent.EventType.CLASS,
            },
            {
                'title': 'Calculus I - Lecture 1',
                'description': 'First lecture of the semester. Introduction to limits.',
                'start_date': now + timedelta(days=3, hours=9),
                'end_date': now + timedelta(days=3, hours=11),
                'course': self.courses[2],
                'created_by': self.teachers[1],
                'event_type': CalendarEvent.EventType.CLASS,
            },
            {
                'title': 'Calculus I - Midterm Exam',
                'description': 'Midterm exam covering limits and derivatives.',
                'start_date': now + timedelta(days=30, hours=9),
                'end_date': now + timedelta(days=30, hours=11),
                'course': self.courses[2],
                'created_by': self.teachers[1],
                'event_type': CalendarEvent.EventType.EXAM,
            },
        ]
        
        for data in events_data:
            event, created = CalendarEvent.objects.get_or_create(
                title=data['title'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                course=data['course'],
                defaults={
                    'description': data['description'],
                    'created_by': data['created_by'],
                    'event_type': data['event_type'],
                }
            )
            if created:
                self.stdout.write(f'Created calendar event: {event.title}')
    
    def print_login_credentials(self):
        """Print login credentials for demo users"""
        self.stdout.write(self.style.SUCCESS('\n--- Demo User Login Credentials ---'))
        self.stdout.write('Admin:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin1234')
        self.stdout.write('\nTeachers:')
        self.stdout.write('  Username: teacher1')
        self.stdout.write('  Password: teacher1234')
        self.stdout.write('  Username: teacher2')
        self.stdout.write('  Password: teacher1234')
        self.stdout.write('\nStudents:')
        self.stdout.write('  Username: student1')
        self.stdout.write('  Password: student1234')
        self.stdout.write('  Username: student2')
        self.stdout.write('  Password: student1234')
        self.stdout.write('  Username: student3')
        self.stdout.write('  Password: student1234')
