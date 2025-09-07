#!/bin/bash

echo "=== Hybrid Quantum-Classical AI Exam Analyzer Setup ==="

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    echo "⚠ Script is running with sudo - this will lose virtual environment context"
    echo "Please run without sudo: ./setup_env.sh"
    echo "If you need permissions, make the script executable: chmod +x setup_env.sh"
    exit 1
fi

# Get the absolute path of the current directory
CURRENT_DIR=$(pwd)
VENV_PATH="$CURRENT_DIR/hybrid-venv"

# Check if virtual environment exists
if [ -d "hybrid-venv" ]; then
    echo "✓ Virtual environment 'hybrid-venv' found"
    
    # Check if we're in a virtual environment and it's the right one
    if [ -n "$VIRTUAL_ENV" ]; then
        # Check if it's our hybrid-venv (compare resolved paths)
        VENV_REAL_PATH=$(realpath "$VIRTUAL_ENV" 2>/dev/null || echo "$VIRTUAL_ENV")
        EXPECTED_REAL_PATH=$(realpath "$VENV_PATH" 2>/dev/null || echo "$VENV_PATH")
        
        if [[ "$VENV_REAL_PATH" == "$EXPECTED_REAL_PATH" ]]; then
            echo "✓ Correct virtual environment is activated"
            echo "  Active environment: $VIRTUAL_ENV"
        else
            echo "⚠ Different virtual environment is active: $VIRTUAL_ENV"
            echo "Expected: $VENV_PATH"
            echo "Please switch to the correct environment:"
            echo "  deactivate"
            echo "  source hybrid-venv/bin/activate"
            exit 1
        fi
    else
        echo "⚠ No virtual environment is activated"
        echo "Please activate hybrid-venv:"
        echo "  source hybrid-venv/bin/activate"
        echo "  ./setup_env.sh"
        exit 1
    fi
else
    echo "✗ Virtual environment 'hybrid-venv' not found"
    echo "Please create it first:"
    echo "  python3 -m venv hybrid-venv"
    echo "  source hybrid-venv/bin/activate"
    echo "  ./setup_env.sh"
    exit 1
fi

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt found"
    
    # Install requirements with better error handling
    echo ""
    echo "=== Installing Python packages from requirements.txt ==="
    echo "This may take several minutes for quantum and ML packages..."
    
    # Upgrade pip first
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install packages with verbose output and error handling
    echo "Installing packages..."
    if pip install -r requirements.txt --verbose; then
        echo "✓ Package installation completed"
    else
        echo "⚠ Some packages may have failed to install"
        echo "Attempting to install critical packages individually..."
        
        # Try installing critical packages one by one
        echo "Installing Django..."
        pip install Django==4.2.7
        
        echo "Installing spaCy..."
        pip install spacy==3.7.2
        
        echo "Installing remaining packages..."
        pip install -r requirements.txt --ignore-installed
    fi

    echo ""
    echo "=== Package Descriptions ==="
    echo ""
    echo "🌐 Web Framework & Database:"
    echo "  • Django==4.2.7           - High-level Python web framework for rapid development"
    echo "  • mysqlclient==2.2.0       - MySQL database adapter for Python"
    echo "  • djangorestframework==3.14.0 - Powerful toolkit for building Web APIs in Django"
    echo "  • django-cors-headers==4.3.1  - Cross-Origin Resource Sharing (CORS) headers for Django"
    echo ""
    echo "⚛️ Quantum Computing:"
    echo "  • qiskit==0.45.0           - Open-source quantum computing framework by IBM"
    echo "  • qiskit-machine-learning==0.7.0 - Machine learning algorithms for quantum computers"
    echo "  • qiskit-aer==0.13.0       - High-performance quantum circuit simulator"
    echo ""
    echo "🧠 Natural Language Processing:"
    echo "  • spacy==3.7.2             - Industrial-strength NLP library with neural models"
    echo "  • nltk==3.8.1              - Natural Language Toolkit for text processing"
    echo "  • sentence-transformers==2.2.2 - State-of-the-art sentence embeddings"
    echo ""
    echo "🤖 Machine Learning & Data Science:"
    echo "  • scikit-learn==1.3.2      - Machine learning library with classification and clustering"
    echo "  • numpy==1.24.3            - Fundamental package for scientific computing"
    echo "  • pandas==2.1.3            - Data manipulation and analysis library"
    echo "  • matplotlib==3.8.2        - Comprehensive plotting library"
    echo "  • seaborn==0.13.0          - Statistical data visualization based on matplotlib"
    echo ""
    echo "📄 Document Processing:"
    echo "  • PyPDF2==3.0.1           - PDF reader and merger for text extraction"
    echo "  • python-docx==0.8.11     - Create and update Microsoft Word documents"
    echo ""
    echo "⚡ Task Processing & Caching:"
    echo "  • celery==5.3.4            - Distributed task queue for background processing"
    echo "  • redis==5.0.1             - In-memory data structure store for caching"
    echo ""
    echo "=== Installation Complete ==="
    echo ""
    echo "🚀 Next Steps:"
    echo "1. Download spaCy language model: python -m spacy download en_core_web_sm"
    echo "2. Setup MySQL database and update settings.py"
    echo "3. Run Django migrations: python manage.py migrate"
    echo "4. Create superuser: python manage.py createsuperuser"
    echo "5. Start development server: python manage.py runserver"
    echo ""
    echo "📚 Key Features Enabled:"
    echo "  ✓ Quantum machine learning with Qiskit"
    echo "  ✓ Advanced NLP with spaCy and sentence transformers"
    echo "  ✓ PDF/DOCX document processing"
    echo "  ✓ High-performance data analysis with NumPy/Pandas"
    echo "  ✓ Web API development with Django REST Framework"
    echo "  ✓ Background task processing with Celery"
    
else
    echo "✗ requirements.txt not found"
    echo "Please ensure requirements.txt exists in the current directory"
    exit 1
fi

# Verify key packages are installed with better error reporting
echo ""
echo "=== Verifying Critical Package Installation ==="

# Function to check package installation
check_package() {
    local package_name=$1
    local import_name=$2
    local version_attr=$3
    
    if python -c "import $import_name; print(f'✓ $package_name {getattr($import_name, '$version_attr', 'unknown')} installed')" 2>/dev/null; then
        return 0
    else
        echo "✗ $package_name installation failed"
        echo "  Attempting to reinstall $package_name..."
        pip install --force-reinstall $package_name
        if python -c "import $import_name" 2>/dev/null; then
            echo "  ✓ $package_name reinstalled successfully"
        else
            echo "  ✗ $package_name reinstallation failed"
            echo "  Please manually install: pip install $package_name"
        fi
        return 1
    fi
}

# Check critical packages
check_package "Django" "django" "__version__"
check_package "Qiskit" "qiskit" "__version__"
check_package "spaCy" "spacy" "__version__"
check_package "scikit-learn" "sklearn" "__version__"

# Additional spaCy model download
echo ""
echo "=== Downloading spaCy Language Model ==="
if python -c "import spacy" 2>/dev/null; then
    echo "Downloading English language model for spaCy..."
    python -m spacy download en_core_web_sm
    if python -c "import spacy; nlp = spacy.load('en_core_web_sm')" 2>/dev/null; then
        echo "✓ spaCy English model installed successfully"
    else
        echo "⚠ spaCy model download may have failed"
        echo "You can manually install it later with: python -m spacy download en_core_web_sm"
    fi
else
    echo "⚠ spaCy not available, skipping model download"
fi

echo ""
echo "🎉 Setup verification complete!"
echo ""
echo "📊 Installation Summary:"
python -c "
import sys
packages = ['django', 'qiskit', 'spacy', 'sklearn', 'numpy', 'pandas']
installed = []
failed = []

for pkg in packages:
    try:
        __import__(pkg)
        installed.append(pkg)
    except ImportError:
        failed.append(pkg)

print(f'✓ Successfully installed: {len(installed)}/{len(packages)} packages')
if installed:
    print(f'  Installed: {', '.join(installed)}')
if failed:
    print(f'✗ Failed packages: {', '.join(failed)}')
    print('  Please manually install failed packages')
"
