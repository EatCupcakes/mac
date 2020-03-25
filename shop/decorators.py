from django.http import HttpResponse
from django.shortcuts import redirect

#a decrator is a function that takes in anther function in as a parameter and lets
#us add a little extra functinality before the original function is called.
def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


# what's happening here is the decorator is gonna be placed on top of a view
#just like we did 
def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):


            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse('You are not authorised to view this page')
        return wrapper_func
    return decorator

def admin_only(view_func):
    def wrapper_func(request, *args, **kwargs):
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name

        if group == 'admin':
            return redirect('user-page')

        if group == 'customer':
            return view_func(request, *args, **kwargs)

    return wrapper_func



