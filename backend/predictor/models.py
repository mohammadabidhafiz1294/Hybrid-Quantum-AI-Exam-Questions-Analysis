from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import json

class Syllabus(models.Model):
    """Model for storing syllabus documents and their extracted topics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='syllabi')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to='syllabi/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    topic_count = models.PositiveIntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    topics_data = models.JSONField(default=dict, blank=True)  # Store extracted topics

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Syllabus'
        verbose_name_plural = 'Syllabi'

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ExamPaper(models.Model):
    """Model for storing exam papers and their analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_papers')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to='exams/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    year = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    question_count = models.PositiveIntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    questions_data = models.JSONField(default=list, blank=True)  # Store segmented questions
    topics_covered = models.JSONField(default=list, blank=True)  # Topics found in exam

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ['user', 'title', 'year']

    def __str__(self):
        return f"{self.title} ({self.year}) - {self.user.username}"

class Topic(models.Model):
    """Model for storing topics extracted from syllabi and their frequency"""
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)  # Additional topic information

    class Meta:
        ordering = ['-frequency', '-last_seen']
        unique_together = ['syllabus', 'name']

    def __str__(self):
        return f"{self.name} ({self.frequency})"

class Prediction(models.Model):
    """Model for storing quantum and classical predictions"""
    PREDICTION_TYPES = [
        ('QUANTUM', 'Quantum VQE Prediction'),
        ('CLASSICAL', 'Classical ML Prediction'),
        ('HYBRID', 'Hybrid Prediction'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=20, choices=PREDICTION_TYPES, default='HYBRID')
    created_at = models.DateTimeField(auto_now_add=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    quantum_result = models.JSONField(default=dict, blank=True)  # VQE results
    classical_result = models.JSONField(default=dict, blank=True)  # Classical ML results
    final_prediction = models.JSONField(default=dict, blank=True)  # Combined/selected result
    description = models.TextField(blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # Time taken for prediction

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.prediction_type} - {self.user.username} ({self.created_at.date()})"
