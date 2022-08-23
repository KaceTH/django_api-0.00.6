from datetime import datetime, timedelta
from random import randint
from django.shortcuts import render

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie 
from rest_framework.parsers import JSONParser
from django.http import JsonResponse

from Authentication.utils import generate_access_token, generate_refresh_token

from django.contrib.auth import authenticate, login
from Authentication.models import User, Verification
from .serializer import CreateUser, EditUser, ReadUser, CreateVerification

from django.core.mail import send_mail
from django.conf import settings

# Create your views here.

@csrf_exempt
@ensure_csrf_cookie
def login(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)

        username = data['user_id']
        password = data['password']
        try :
            loginUser = User.objects.get(username=username, password=password)
        except :
            return JsonResponse({
                "code" : "00101",
                "message" : "해당하는 사용자 아이디 또는 비밀번호가 존재하지 않습니다. ",
                "status" : 404
            })
        
        access_token = generate_access_token(loginUser)
        refresh_token = generate_refresh_token(loginUser)

        tokens = dict(
            user_id=username,
            name=loginUser.name,
            access_token=access_token,
            refresh_token=refresh_token
        )
        res = dict(
            code="10101",
            message="로그인이 완료되었습니다.",
            status=200,
            info = tokens
        )
        return JsonResponse(
            res, safe=False,status=200
        )

    else :
        message = "You must send 'POST' request"
        res = dict(
            code="00105",
            message=message,
            status=301
        )
        return JsonResponse(
            res, safe=False, status=301
        )


@csrf_exempt
def signUp(request):
    data = JSONParser().parse(request)

    if request.method == 'POST':
        try :
            User.objects.get(username=data['user_id'])
            return JsonResponse({
                "code" : "00201",
                "message" : "해당 아이디는 중복됩니다.",
                "status" : 405
            }, status=400)
        except :
            pass

        try :
            User.objects.get(email=data['email'])
            return JsonResponse({
            	"code" : "00203",
	            "message" : "메일인증을 실패하였습니다.",
	            "status" : 400
            }, status=400)
        except :
            pass

        try :
            User.objects.get(
                grade_number    = data['grade_number'],
                class_number    = data['class_number'],
                student_number  = data['student_number']
            )
            return JsonResponse({
            	"code" : "00202",
	            "message" : "해당 학생 또는 학생번호를 이용하는 사용자가 이미 존재합니다.",
	            "status" : 405
            }, status=400)
        except :
            pass

        serializer = CreateUser(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "code" : "10201",
	            "message" : "회원가입이 완료 되었습니다.",
                "status" : 201,
                "info" : serializer.data
            }, safe=False, status=201)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
#@permission_classes((IsAuthenticated, ))
@csrf_exempt
def user_setting(request, username):
    try:
        getUser = User.objects.get(username=username)
    except :
        return JsonResponse({
        "code" : "00702",
        "message" : f"{username}라는 유저는 존재하지않습니다.",
        "status": 404 
    })
        
    if request.method == 'GET':
        serializer = ReadUser(getUser)
        return JsonResponse({	
            "code" : "10701",
	        "message" : "회원정보를 불러왔습니다.",
	        "status" : 200,
            "info" : serializer.data
        }, safe=False, status=200)
    
    if request.method == 'PUT':
        data = JSONParser().parse(request)

        try :
            User.objects.get(email=data['email'])
            return JsonResponse({
            	"code" : "00704",
	            "message" : "메일을 이용중인 사용자가 이미 존재합니다.",
	            "status": 400
            }, status=400)
        except :
            pass

        try :
            User.objects.get(
                grade_number    = data['grade_number'],
                class_number    = data['class_number'],
                student_number  = data['student_number']
            )
            return JsonResponse({
                "code" : "00705",
                "message" : "해당 학생 또는 학생번호를 이용하는 사용자가 이미 존재합니다.",
                "status" : 405
            }, status=405)
        except :
            pass
        
        serializer = EditUser(getUser, data=data)

        if serializer.is_valid():
            serializer.save()
        return JsonResponse({
            "code" : "10702",
	        "message" : "회원정보가 바뀌었습니다.",
	        "status" : 201,
            "info" : serializer.data
        }, safe=False, status=201)
    
    if request.method == 'DELETE':
        data = JSONParser().parse(request)

        if getUser.password == data['password']:
            getUser.delete()
            return JsonResponse({
                "code" : "10703",
	            "message" : "회원 탈퇴가 정상적으로 완료되었습니다.",
	            "status" : 200
            })
        else :
            return JsonResponse({
                "code" : "00703",
	            "message" : "비밀번호가 일치 하지 않습니다.",
	            "status": 400
            }, status=400)

    return JsonResponse({
        "message" : "You must send ['GET', 'POST', 'DELETE'] request"
    }, safe=False, status=301)

@csrf_exempt
def email_verification(request, username):
    try:
        getUser = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({
	        "code" : "00302",
	        "message" : f"{username} 라는 유저는 존재하지않습니다.",
	        "status": 404 
        }, status=404)

    if request.method == 'GET':
        if getUser.is_verificated == True :
            return JsonResponse({
                "code" : "00303",
                "message" : "메일 인증을 이미 완료하였습니다",
                "status": 403 
            })

        code = randint(123456,999999)

        try :
            getVerific = Verification.objects.get(author=getUser)
            getVerific.delete()
        except Verification.DoesNotExist:
            pass

        verification = Verification.objects.create(
            author=getUser,
            code=code,
        )
        verification.send_verification()
        verification.set_end_date()

        info = dict(user_id=username, email=getUser.email)

        return JsonResponse({
            "code" : "10301",
            "message" : "메일인증코드를 전송하였습니다.",
            "status" : 200,
            "info" : info
        })

    if request.method == 'POST':
        try :
            getVerific = Verification.objects.get(author=getUser)
        except Verification.DoesNotExist:
            return JsonResponse({
                "code" : "00304",
                "message" : "메일 인증이 존재하지 않습니다.",
                "status": 400
            })

        data = JSONParser().parse(request)
        if getVerific.is_end_date() == True:
            return JsonResponse({
                "code" : "00305",
                "message" : "기간이 만료되었습니다.",
                "status": 400
            })

        if data['code'] == getVerific.code :
            getVerific.delete()
            getUser.is_verificated = True
            getUser.save()

            return JsonResponse({
                "code" : "10302",
                "message" : "메일인증을 완료하였습니다.",
                "status" : 200,
            })
        return JsonResponse({
            "error" : "wa",
        })


@csrf_exempt
def find_pw(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)

        username = data['user_id']
        email = data['email']

        try :
            getUser = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            return JsonResponse({
                "code" : "00401",
                "message" : "일치 하는 사용자가 존재하지 않습니다.",
                "status" : 404,
            }, status=404)
        
        message = f"your password is '{getUser.password}'"
        title = f"{getUser.username}'s password"

        send_mail(
            title,
            message,
            settings.EMAIL_HOST_USER,
            [getUser.email]
        )
        return JsonResponse({
            "code" : "10401",
            "message" : "메일에 비밀번호를 전송하였습다.",
            "status" : 400
        })
    return JsonResponse({
        "message" : "You must send ['POST'] request"
    }, safe=False, status=301)
