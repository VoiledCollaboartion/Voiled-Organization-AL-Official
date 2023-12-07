from django.shortcuts import render,redirect

from django.http import HttpResponse
from django.contrib.auth.models import User,auth
from django.contrib import messages

# Create your views here.


def signup(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        skills = request.POST['skills']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')

            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username Taken')

            else:
                user = User.objects.create_user(username=username,email=email,password=password,first_name=skills)
                user.save()
                messages.info(request,'Member Registered')


                #log userin and redirect
                user_login = auth.authenticate(username=username,password=password)
                auth.login(request,user_login)


                return redirect('signup')

        else:
            messages.info(request, 'Password Not matching')
            return redirect('signup')


    else:
        return render(request,'signup.html')



