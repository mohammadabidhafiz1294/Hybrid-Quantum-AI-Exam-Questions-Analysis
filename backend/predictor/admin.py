from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Syllabus, ExamPaper, Topic, Prediction

# Unregister the default User admin
admin.site.unregister(User)

# Register the default User admin with customizations
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'uploaded_at', 'processed', 'topic_count')
    list_filter = ('processed', 'uploaded_at', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('uploaded_at', 'processed_at')
    ordering = ('-uploaded_at',)

@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'year', 'uploaded_at', 'question_count')
    list_filter = ('year', 'uploaded_at', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'syllabus', 'frequency', 'last_seen')
    list_filter = ('syllabus__title', 'last_seen')
    search_fields = ('name', 'description', 'syllabus__title')
    readonly_fields = ('created_at', 'last_seen')
    ordering = ('-frequency',)

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'accuracy_score', 'prediction_type')
    list_filter = ('prediction_type', 'created_at', 'user')
    search_fields = ('user__username', 'description')
    readonly_fields = ('created_at', 'quantum_result', 'classical_result')
    ordering = ('-created_at',)

# Custom admin site header
admin.site.site_header = 'EduQuantum Predictor Administration'
admin.site.site_title = 'EduQuantum Admin'
admin.site.index_title = 'EduQuantum Dashboard'
