from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
    path('django/', views.dashboard, name='dashboard'),  # Relocated to /django/ prefix
    path('django/login/', views.login_view, name='login'),
    path('django/register/', views.register_view, name='register'),
    path('django/logout/', views.logout_view, name='logout'),
    path('django/profile/', views.profile, name='profile'),
    path('django/courses/', views.courses, name='courses'),
    path('django/manage-courses/', views.manage_courses, name='manage_courses'),
    path('django/calendar/', views.calendar, name='calendar'),
    path('django/announcements/', views.announcements, name='announcements'),
    path('django/kanban/', views.kanban, name='kanban'),
    path('django/reports/', views.reports, name='reports'),
    path('django/user-management/', views.user_management, name='user_management'),
    path('django/role-demo/', views.role_demo, name='role_demo'),
    
    # Course routes
    path('django/course/<int:pk>/', views.course_detail, name='course_detail'),
    path('django/course/create/', views.create_course, name='create_course'),
    path('django/course/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('django/course/<int:pk>/students/', views.course_students, name='course_students'),
    path('django/course/<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('django/announcement/<uuid:pk>/', views.announcement_detail, name='announcement_detail'),
    
    # Next.js frontend (should be last to catch all other routes)
    path('', views.frontend_view, name='frontend'),
    path('<path:path>', views.frontend_view, name='frontend_path'),
]
