from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from .models import Agent
from .mqtt_handler import agent_sensor_data, agent_last_frame, sensor_data_lock, frame_lock, mqtt_client
import json
import cv2
import time

@login_required
def dashboard(request):
    agents = request.user.agents.all()
    return render(request, 'cradle/dashboard.html', {'agents': agents})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'cradle/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'cradle/login.html', {'error': '아이디 또는 비밀번호가 틀렸습니다.'})
    return render(request, 'cradle/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def register_cradle(request):
    if request.method == 'POST':
        cradle_uuid = request.POST['cradle_uuid']
        try:
            agent = Agent.objects.get(uuid=cradle_uuid)
            agent.user = request.user
            agent.save()
            return redirect('dashboard')
        except Agent.DoesNotExist:
            return render(request, 'cradle/register_cradle.html', {'error': '등록되지 않은 UUID입니다.'})
    return render(request, 'cradle/register_cradle.html')

def register_agent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        agent_uuid = data.get('uuid')
        agent_ip = data.get('ip')
        if agent_uuid and agent_ip:
            agent, created = Agent.objects.get_or_create(uuid=agent_uuid, defaults={'ip': agent_ip})
            if not created:
                agent.ip = agent_ip
                agent.save()
            return JsonResponse({'status': 'success', 'message': '에이전트 등록 성공'})
    return JsonResponse({'status': 'error', 'message': 'UUID 또는 IP 주소가 제공되지 않았습니다.'})

@login_required
def video_feed(request, uuid):
    def generate():
        while True:
            with frame_lock:
                frame = agent_last_frame.get(uuid)
                if frame is not None:
                    frame = cv2.resize(frame, (640, 480))
                    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.1)
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')

@login_required
def control_motor(request, uuid):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        if action in ['start', 'stop']:
            topic = f"cradle/{uuid}/servo"
            payload = json.dumps({'action': action})
            mqtt_client.publish(topic, payload)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': '잘못된 요청'})

@login_required
def crying_status(request, uuid):
    def generate():
        while True:
            with sensor_data_lock:
                status = agent_sensor_data.get(uuid, {}).get('crying', '측정 중...')
            yield f"data: {status}\n\n"
            time.sleep(1)
    return StreamingHttpResponse(generate(), content_type='text/event-stream')

@login_required
def direction_status(request, uuid):
    def generate():
        while True:
            with sensor_data_lock:
                direction = agent_sensor_data.get(uuid, {}).get('direction', '측정 중...')
            yield f"data: {direction}\n\n"
            time.sleep(1)
    return StreamingHttpResponse(generate(), content_type='text/event-stream')

@login_required
def get_sensor_data(request, uuid):
    with sensor_data_lock:
        data = agent_sensor_data.get(uuid, {
            "crying": None,
            "direction": None,
            "temperature": None
        })
    return JsonResponse(data)
