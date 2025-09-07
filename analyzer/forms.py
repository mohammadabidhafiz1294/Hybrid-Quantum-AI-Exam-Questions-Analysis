from django import forms
from .models import Syllabus, ExamPaper, Course

class SyllabusUploadForm(forms.ModelForm):
    class Meta:
        model = Syllabus
        fields = ['course', 'title', 'file', 'year']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter syllabus title'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2030}),
        }

class ExamPaperUploadForm(forms.ModelForm):
    class Meta:
        model = ExamPaper
        fields = ['course', 'title', 'file', 'year', 'semester', 'exam_type']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter exam title'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2030}),
            'semester': forms.Select(
                choices=[('fall', 'Fall'), ('spring', 'Spring'), ('summer', 'Summer')],
                attrs={'class': 'form-control'}
            ),
            'exam_type': forms.Select(
                choices=[('midterm', 'Midterm'), ('final', 'Final'), ('quiz', 'Quiz')],
                attrs={'class': 'form-control'}
            ),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }
