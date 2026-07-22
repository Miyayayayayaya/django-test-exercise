from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task


LAYOUT_VERTICAL = 'vertical'
LAYOUT_HORIZONTAL = 'horizontal'
LAYOUT_SESSION_KEY = 'todo_layout'
THEME_TONE_SESSION_KEY = 'todo_theme_tone'
THEME_TONE_DEFAULT = 100
THEME_HUE_COOL = 200
THEME_HUE_WARM = 20


def get_layout(request):
    layout = request.session.get(LAYOUT_SESSION_KEY, LAYOUT_VERTICAL)
    if layout not in {LAYOUT_VERTICAL, LAYOUT_HORIZONTAL}:
        return LAYOUT_VERTICAL
    return layout


def _parse_theme_tone(raw_value):
    if raw_value in {None, ''}:
        return THEME_TONE_DEFAULT
    try:
        tone = int(raw_value)
    except (TypeError, ValueError):
        return THEME_TONE_DEFAULT
    return max(0, min(100, tone))


def get_theme_tone(request):
    return _parse_theme_tone(request.session.get(THEME_TONE_SESSION_KEY, THEME_TONE_DEFAULT))


def get_theme_hue(request):
    tone = get_theme_tone(request)
    return round(THEME_HUE_COOL - ((THEME_HUE_COOL - THEME_HUE_WARM) * tone / 100))


def get_theme_context(request):
    tone = get_theme_tone(request)
    return {
        'theme_tone': tone,
        'theme_hue': round(THEME_HUE_COOL - ((THEME_HUE_COOL - THEME_HUE_WARM) * tone / 100)),
    }


def _parse_rating(raw_value):
    if raw_value in {None, ''}:
        return 0
    try:
        rating = int(raw_value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, rating))


def index(request):
    if request.method == 'POST':
        due_value = request.POST.get('due_at')
        due_at = make_aware(parse_datetime(due_value)) if due_value else None
        task = Task(
            title=request.POST['title'],
            due_at=due_at,
            rating=_parse_rating(request.POST.get('rating')),
        )
        task.save()

    if request.GET.get('order') == 'due':
        tasks = Task.objects.order_by('due_at')
    else:
        tasks = Task.objects.order_by('-posted_at')

    context = {
        'tasks': tasks,
        'layout': get_layout(request),
    }
    context.update(get_theme_context(request))
    return render(request, 'todo/index.html', context)


def settings(request):
    if request.method == 'POST':
        if 'theme_tone' in request.POST:
            theme_tone = _parse_theme_tone(request.POST.get('theme_tone'))
            request.session[THEME_TONE_SESSION_KEY] = theme_tone
            return JsonResponse({
                'theme_tone': theme_tone,
                'theme_hue': round(THEME_HUE_COOL - ((THEME_HUE_COOL - THEME_HUE_WARM) * theme_tone / 100)),
            })
        layout = request.POST.get('layout', LAYOUT_VERTICAL)
        if layout in {LAYOUT_VERTICAL, LAYOUT_HORIZONTAL}:
            request.session[LAYOUT_SESSION_KEY] = layout
        return redirect('settings')

    context = {
        'layout': get_layout(request),
        'vertical_layout': LAYOUT_VERTICAL,
        'horizontal_layout': LAYOUT_HORIZONTAL,
    }
    context.update(get_theme_context(request))
    return render(request, 'todo/settings.html', context)


def detail(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        'task': task,
    }
    context.update(get_theme_context(request))
    return render(request, 'todo/detail.html', context)


def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == 'POST':
        task.title = request.POST['title']
        due_value = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_value)) if due_value else None
        task.rating = _parse_rating(request.POST.get('rating'))
        task.save()
        return redirect(detail, task_id)

    context = {
        'task': task
    }
    context.update(get_theme_context(request))
    return render(request, "todo/edit.html", context)

def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task. delete()
    return redirect(index)
