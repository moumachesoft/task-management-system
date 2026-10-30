from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Task
from django.db.models import Q
from datetime import date, timedelta
from .forms import TaskForm

# User Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task-list')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

# Task List & Filtering/Searching
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(owner=self.request.user)
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
            
        priority = self.request.GET.get('priority', '')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        due_date_filter = self.request.GET.get('due_date', '')
        today = date.today()
        if due_date_filter == 'today':
            queryset = queryset.filter(due_date=today)
        elif due_date_filter == 'this_week':
            end_of_week = today + timedelta(days=7)
            queryset = queryset.filter(due_date__range=[today, end_of_week])
        elif due_date_filter == 'overdue':
            queryset = queryset.filter(due_date__lt=today).exclude(status='Completed')

        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'

    def test_func(self):
        return self.request.user == self.get_object().owner

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'tasks/task_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    template_name = 'tasks/task_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('task-list')

    def test_func(self):
        return self.request.user == self.get_object().owner

class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

    def test_func(self):
        return self.request.user == self.get_object().owner