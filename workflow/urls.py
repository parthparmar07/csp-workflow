from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.views.generic.base import RedirectView

# Setup API routes using DRF router
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'calendar-events', views.CalendarEventViewSet)
router.register(r'announcements', views.AnnouncementViewSet)
router.register(r'kanban-boards', views.KanbanBoardViewSet)
router.register(r'kanban-columns', views.KanbanColumnViewSet)
router.register(r'kanban-cards', views.KanbanCardViewSet)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/csrf/', views.get_csrf_token, name='csrf_token'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/user/', views.current_user_api, name='current_user_api'),
    path('api/register/', views.register_api, name='register_api'),
    
    # Django original views
    path('', RedirectView.as_view(url='/login/', permanent=False), name='home'),  # Redirect root to login
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('courses/', views.courses, name='courses'),
    path('manage-courses/', views.manage_courses, name='manage_courses'),
    path('calendar/', views.calendar, name='calendar'),
    path('announcements/', views.announcements, name='announcements'),
    path('kanban/', views.kanban, name='kanban'),
    path('reports/', views.reports, name='reports'),
    path('user-management/', views.user_management, name='user_management'),
    path('role-demo/', views.role_demo, name='role_demo'),
    
    # Course routes
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('course/<int:pk>/students/', views.course_students, name='course_students'),
    path('course/<int:pk>/delete/', views.delete_course, name='delete_course'),
    
    # Announcement routes
    path('announcement/<uuid:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    
    # User management routes
    path('user/create/', views.create_user, name='create_user'),
]
