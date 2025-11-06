from django.shortcuts import render
from django.http import HttpRequest


def index(request: HttpRequest):
    return render(request, "demo_kawaki/index.html", {"title": "Demo Kawaki"})

# Create your views here.
