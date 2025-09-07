from django.db import models
from django.contrib.auth.models import User
import json

class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Syllabus(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='syllabi/')
    extracted_text = models.TextField(blank=True)
    processed_topics = models.JSONField(default=list)
    year = models.IntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Topic(models.Model):
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE)
    name = models.CharField(max_length=300)
    chapter_number = models.IntegerField(null=True, blank=True)
    keywords = models.JSONField(default=list)
    importance_score = models.FloatField(default=0.0)
    embedding_vector = models.JSONField(default=list)

class ExamPaper(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='exams/')
    extracted_text = models.TextField(blank=True)
    year = models.IntegerField()
    semester = models.CharField(max_length=20)
    exam_type = models.CharField(max_length=50)  # midterm, final, quiz
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    exam_paper = models.ForeignKey(ExamPaper, on_delete=models.CASCADE)
    text = models.TextField()
    question_number = models.IntegerField()
    marks = models.IntegerField(null=True, blank=True)
    question_type = models.CharField(max_length=50)  # MCQ, short, long
    mapped_topics = models.ManyToManyField(Topic, through='QuestionTopicMapping')
    embedding_vector = models.JSONField(default=list)

class QuestionTopicMapping(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    similarity_score = models.FloatField()
    confidence = models.FloatField()
    quantum_score = models.FloatField(null=True, blank=True)

class TopicTrend(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    year = models.IntegerField()
    frequency = models.IntegerField(default=0)
    importance_trend = models.FloatField(default=0.0)
    quantum_pattern_score = models.FloatField(null=True, blank=True)

class PredictionResult(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    target_year = models.IntegerField()
    predicted_topics = models.JSONField()
    confidence_scores = models.JSONField()
    quantum_circuit_results = models.JSONField()
    classical_ml_results = models.JSONField()
    hybrid_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
