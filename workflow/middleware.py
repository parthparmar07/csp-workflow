from django.contrib.auth.models import User
from django.utils.functional import cached_property

class UserRoleMiddleware:
    """
    Middleware to add role flags to the user object for easy template access
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Add role flags to the user object
        if request.user.is_authenticated:
            self._setup_user_role_properties(request.user)
        
        response = self.get_response(request)
        return response
    
    def _setup_user_role_properties(self, user):
        """Set up role properties on the user object"""
        # Check if user has the role attribute (using custom User model)
        if hasattr(user, 'role'):
            # Use the role attribute from the custom User model
            setattr(user, '_is_admin', user.role == 'ADMIN')
            setattr(user, '_is_teacher', user.role == 'TEACHER')
            setattr(user, '_is_student', user.role == 'STUDENT')
        else:
            # Fallback to the old behavior if using the default User model
            setattr(user, '_is_admin', user.is_staff and user.is_superuser)
            setattr(user, '_is_teacher', user.is_staff and not user.is_superuser)
            setattr(user, '_is_student', not user.is_staff)
        
        # Add method for getting user initials for avatar
        if not hasattr(user, 'get_initials'):
            setattr(user, 'get_initials', self._create_get_initials_function(user))
    
    def _create_get_initials_function(self, user):
        """Create a function to get user initials"""
        def get_initials():
            full_name = user.get_full_name().split()
            if full_name:
                return ''.join([n[0].upper() for n in full_name if n])
            return user.username[0].upper() if user.username else '?'
        return get_initials

# Define properties instead of directly setting attributes on the User model
def is_admin(self):
    """Property to check if user is an admin"""
    return getattr(self, '_is_admin', False)

def is_teacher(self):
    """Property to check if user is a teacher"""
    return getattr(self, '_is_teacher', False)

def is_student(self):
    """Property to check if user is a student"""
    return getattr(self, '_is_student', False)

# Add these properties to the User model - but only if they don't already exist
if not hasattr(User, 'is_admin'):
    User.is_admin = property(is_admin)
    
if not hasattr(User, 'is_teacher'):
    User.is_teacher = property(is_teacher)
    
if not hasattr(User, 'is_student'):
    User.is_student = property(is_student)
