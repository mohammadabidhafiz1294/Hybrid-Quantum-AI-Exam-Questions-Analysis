from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import *
from .forms import SyllabusUploadForm, ExamPaperUploadForm
from .nlp_processor import SyllabusProcessor, QuestionProcessor
from .quantum_processor import HybridQuantumClassical
import json
import os

@login_required
def dashboard(request):
    """Main dashboard view"""
    courses = Course.objects.all()
    recent_syllabi = Syllabus.objects.order_by('-created_at')[:5]
    recent_exams = ExamPaper.objects.order_by('-created_at')[:5]
    
    context = {
        'courses': courses,
        'recent_syllabi': recent_syllabi,
        'recent_exams': recent_exams,
        'total_courses': courses.count(),
        'total_syllabi': Syllabus.objects.count(),
        'total_exams': ExamPaper.objects.count(),
    }
    return render(request, 'analyzer/dashboard.html', context)

@login_required
def upload_syllabus(request):
    """Handle syllabus file upload and processing"""
    if request.method == 'POST':
        form = SyllabusUploadForm(request.POST, request.FILES)
        if form.is_valid():
            syllabus = form.save(commit=False)
            syllabus.uploaded_by = request.user
            
            # Extract text from uploaded file
            processor = SyllabusProcessor()
            file_path = syllabus.file.path
            extracted_text = processor.extract_text_from_file(file_path)
            syllabus.extracted_text = extracted_text
            
            # Process topics
            topics_data = processor.identify_topics_and_chapters(extracted_text)
            syllabus.processed_topics = topics_data
            syllabus.save()
            
            # Create Topic objects
            for topic_data in topics_data:
                Topic.objects.create(
                    syllabus=syllabus,
                    name=topic_data['name'],
                    chapter_number=topic_data.get('chapter_number'),
                    keywords=topic_data['keywords'],
                    embedding_vector=topic_data['embedding_vector']
                )
            
            messages.success(request, f'Syllabus uploaded and processed successfully! Found {len(topics_data)} topics.')
            return redirect('syllabus_detail', pk=syllabus.pk)
    else:
        form = SyllabusUploadForm()
    
    return render(request, 'analyzer/upload_syllabus.html', {'form': form})

@login_required
def upload_exam(request):
    """Handle exam paper upload and processing"""
    if request.method == 'POST':
        form = ExamPaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.uploaded_by = request.user
            
            # Extract text from uploaded file
            processor = SyllabusProcessor()
            file_path = exam.file.path
            extracted_text = processor.extract_text_from_file(file_path)
            exam.extracted_text = extracted_text
            exam.save()
            
            # Extract questions
            question_processor = QuestionProcessor()
            questions_data = question_processor.extract_questions_from_text(extracted_text)
            
            # Create Question objects
            for q_data in questions_data:
                Question.objects.create(
                    exam_paper=exam,
                    text=q_data['text'],
                    question_number=q_data['number'],
                    embedding_vector=q_data['embedding_vector']
                )
            
            messages.success(request, f'Exam paper uploaded successfully! Found {len(questions_data)} questions.')
            return redirect('exam_detail', pk=exam.pk)
    else:
        form = ExamPaperUploadForm()
    
    return render(request, 'analyzer/upload_exam.html', {'form': form})

@login_required
def analyze_course(request, course_id):
    """Perform quantum-enhanced analysis for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Get all syllabi and exams for the course
    syllabi = Syllabus.objects.filter(course=course)
    exams = ExamPaper.objects.filter(course=course)
    
    if not syllabi.exists() or not exams.exists():
        messages.warning(request, 'Please upload both syllabi and exam papers before analysis.')
        return redirect('dashboard')
    
    # Perform question-topic mapping
    question_processor = QuestionProcessor()
    
    for exam in exams:
        questions = Question.objects.filter(exam_paper=exam)
        for syllabus in syllabi:
            topics = Topic.objects.filter(syllabus=syllabus)
            
            # Convert to format expected by processor
            questions_data = [
                {
                    'number': q.question_number,
                    'text': q.text,
                    'embedding_vector': q.embedding_vector
                }
                for q in questions
            ]
            
            topics_data = [
                {
                    'name': t.name,
                    'embedding_vector': t.embedding_vector
                }
                for t in topics
            ]
            
            # Map questions to topics
            mappings = question_processor.map_questions_to_topics(questions_data, topics_data)
            
            # Save mappings
            for mapping in mappings:
                question = questions.get(question_number=mapping['question_id'])
                topic = topics.get(name=mapping['topic_name'])
                
                QuestionTopicMapping.objects.get_or_create(
                    question=question,
                    topic=topic,
                    defaults={
                        'similarity_score': mapping['similarity_score'],
                        'confidence': mapping['confidence']
                    }
                )
    
    # Prepare data for quantum analysis
    topic_trends = {}
    for syllabus in syllabi:
        topics = Topic.objects.filter(syllabus=syllabus)
        for topic in topics:
            if topic.name not in topic_trends:
                topic_trends[topic.name] = []
            
            # Count questions mapped to this topic by year
            year_count = Question.objects.filter(
                mapped_topics=topic,
                exam_paper__year=syllabus.year
            ).count()
            topic_trends[topic.name].append(year_count)
    
    # Perform hybrid quantum-classical analysis
    hybrid_analyzer = HybridQuantumClassical()
    analysis_results = hybrid_analyzer.hybrid_analysis(topic_trends, {})
    
    # Save prediction results
    PredictionResult.objects.create(
        course=course,
        target_year=max([s.year for s in syllabi]) + 1,
        predicted_topics=list(analysis_results.keys()),
        confidence_scores=[r['confidence'] for r in analysis_results.values()],
        quantum_circuit_results=analysis_results,
        classical_ml_results={},
        hybrid_score=sum(r['hybrid_score'] for r in analysis_results.values()) / len(analysis_results)
    )
    
    messages.success(request, 'Analysis completed successfully!')
    return redirect('analysis_results', course_id=course.id)

@login_required
def analysis_results(request, course_id):
    """Display analysis results with visualizations"""
    course = get_object_or_404(Course, id=course_id)
    latest_prediction = PredictionResult.objects.filter(course=course).order_by('-created_at').first()
    
    if not latest_prediction:
        messages.warning(request, 'No analysis results found. Please run analysis first.')
        return redirect('analyze_course', course_id=course_id)
    
    # Prepare data for visualization
    chart_data = {
        'topics': latest_prediction.predicted_topics,
        'confidence_scores': latest_prediction.confidence_scores,
        'quantum_scores': [
            latest_prediction.quantum_circuit_results[topic]['quantum_component']
            for topic in latest_prediction.predicted_topics
        ],
        'classical_scores': [
            latest_prediction.quantum_circuit_results[topic]['classical_component']
            for topic in latest_prediction.predicted_topics
        ]
    }
    
    context = {
        'course': course,
        'prediction': latest_prediction,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'analyzer/analysis_results.html', context)

def api_course_analysis(request, course_id):
    """REST API endpoint for course analysis data"""
    course = get_object_or_404(Course, id=course_id)
    latest_prediction = PredictionResult.objects.filter(course=course).order_by('-created_at').first()
    
    if not latest_prediction:
        return JsonResponse({'error': 'No analysis results found'}, status=404)
    
    return JsonResponse({
        'course_name': course.name,
        'course_code': course.code,
        'prediction_date': latest_prediction.created_at.isoformat(),
        'target_year': latest_prediction.target_year,
        'hybrid_score': latest_prediction.hybrid_score,
        'results': latest_prediction.quantum_circuit_results
    })
