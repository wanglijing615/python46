from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from apps.users.models import UserModel


class HomePage(View):
    def get(self, request):
        return render(request, 'index.html')

