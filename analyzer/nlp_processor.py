import spacy
import nltk
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
import PyPDF2
from docx import Document
import numpy as np

class SyllabusProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
        self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def extract_text_from_file(self, file_path):
        """Extract text from PDF or DOCX files"""
        text = ""
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        elif file_path.endswith('.docx'):
            doc = Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text

    def identify_topics_and_chapters(self, text):
        """Extract structured topics and chapters from syllabus text"""
        doc = self.nlp(text)
        
        # Patterns for chapter/topic identification
        chapter_patterns = [
            r'(?i)chapter\s+(\d+)[:.]?\s*([^\n]+)',
            r'(?i)unit\s+(\d+)[:.]?\s*([^\n]+)',
            r'(?i)module\s+(\d+)[:.]?\s*([^\n]+)',
            r'(?i)(\d+)\.?\s+([A-Z][^\n]+)'
        ]
        
        topics = []
        
        for pattern in chapter_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                chapter_num = int(match.group(1)) if match.group(1).isdigit() else None
                topic_name = match.group(2).strip()
                
                # Extract keywords using NLP
                topic_doc = self.nlp(topic_name)
                keywords = [token.lemma_.lower() for token in topic_doc 
                           if token.pos_ in ['NOUN', 'ADJ'] and not token.is_stop]
                
                # Generate embedding
                embedding = self.sentence_transformer.encode(topic_name).tolist()
                
                topics.append({
                    'name': topic_name,
                    'chapter_number': chapter_num,
                    'keywords': keywords,
                    'embedding_vector': embedding
                })
        
        return topics

    def calculate_topic_importance(self, topics, exam_texts):
        """Calculate importance scores based on historical exam frequency"""
        all_text = ' '.join(exam_texts)
        importance_scores = []
        
        for topic in topics:
            score = 0
            topic_keywords = topic['keywords']
            
            # Count keyword occurrences in exam texts
            for keyword in topic_keywords:
                score += all_text.lower().count(keyword.lower())
            
            # Normalize by topic length
            score = score / max(len(topic_keywords), 1)
            importance_scores.append(score)
        
        # Normalize scores to 0-1 range
        max_score = max(importance_scores) if importance_scores else 1
        normalized_scores = [score / max_score for score in importance_scores]
        
        return normalized_scores

class QuestionProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
    
    def extract_questions_from_text(self, text):
        """Extract individual questions from exam paper text"""
        # Pattern for question identification
        question_patterns = [
            r'(?i)(?:question|q\.?)\s*(\d+)[:.]?\s*([^?]+\?)',
            r'(\d+)\.?\s+([A-Z][^?]+\?)',
            r'(\d+)\)\s*([A-Z][^?]+\?)'
        ]
        
        questions = []
        for pattern in question_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                q_num = int(match.group(1))
                q_text = match.group(2).strip()
                
                # Generate embedding for question
                embedding = self.sentence_transformer.encode(q_text).tolist()
                
                questions.append({
                    'number': q_num,
                    'text': q_text,
                    'embedding_vector': embedding
                })
        
        return questions
    
    def map_questions_to_topics(self, questions, topics, threshold=0.3):
        """Map questions to topics using semantic similarity"""
        mappings = []
        
        for question in questions:
            q_embedding = np.array(question['embedding_vector'])
            
            for topic in topics:
                t_embedding = np.array(topic['embedding_vector'])
                
                # Calculate cosine similarity
                similarity = np.dot(q_embedding, t_embedding) / (
                    np.linalg.norm(q_embedding) * np.linalg.norm(t_embedding)
                )
                
                if similarity > threshold:
                    mappings.append({
                        'question_id': question['number'],
                        'topic_name': topic['name'],
                        'similarity_score': float(similarity),
                        'confidence': min(similarity * 1.2, 1.0)  # Boost confidence slightly
                    })
        
        return mappings
