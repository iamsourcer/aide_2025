from django.shortcuts import render
from app.models import Candidate
from typing import List 
from ninja import NinjaAPI, ModelSchema, Schema

api = NinjaAPI()

@api.get("/hello")
def test(request):
    return "Hello world"
# Create your views here.p
