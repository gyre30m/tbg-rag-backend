#!/usr/bin/env python3
"""
Simple test script to validate the backend structure without dependencies.
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all expected files exist."""
    base_path = Path(__file__).parent
    
    expected_files = [
        "requirements.txt",
        ".env.example",
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/core/security.py",
        "app/models/__init__.py",
        "app/models/enums.py",
        "app/models/documents.py",
        "app/models/processing.py",
        "app/services/__init__.py",
        "app/services/file_service.py",
        "app/services/extraction_service.py",
        "app/services/ai_service.py",
        "app/services/embedding_service.py",
        "app/services/processing_service.py",
        "app/api/__init__.py",
        "app/api/documents.py",
        "app/api/processing.py",
        "app/api/webhooks.py",
        "app/utils/__init__.py",
        "app/utils/file_utils.py"
    ]
    
    print("📁 Checking file structure...")
    missing_files = []
    
    for file_path in expected_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} files missing!")
        return False
    else:
        print(f"\n✅ All {len(expected_files)} files present!")
        return True

def test_python_syntax():
    """Test that all Python files have valid syntax."""
    base_path = Path(__file__).parent
    python_files = list(base_path.rglob("*.py"))
    
    print(f"\n🐍 Checking Python syntax for {len(python_files)} files...")
    
    errors = []
    for py_file in python_files:
        if py_file.name == "test_structure.py":
            continue  # Skip this test file
            
        try:
            with open(py_file, 'r') as f:
                source = f.read()
            compile(source, str(py_file), 'exec')
            print(f"✓ {py_file.relative_to(base_path)}")
        except SyntaxError as e:
            print(f"✗ {py_file.relative_to(base_path)} - Syntax Error: {e}")
            errors.append((py_file, e))
        except Exception as e:
            print(f"✗ {py_file.relative_to(base_path)} - Error: {e}")
            errors.append((py_file, e))
    
    if errors:
        print(f"\n❌ {len(errors)} files have syntax errors!")
        return False
    else:
        print(f"\n✅ All Python files have valid syntax!")
        return True

def count_lines_of_code():
    """Count total lines of code."""
    base_path = Path(__file__).parent
    python_files = [f for f in base_path.rglob("*.py") if f.name != "test_structure.py"]
    
    total_lines = 0
    total_files = 0
    
    print(f"\n📊 Code statistics:")
    
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                lines = len(f.readlines())
            total_lines += lines
            total_files += 1
            print(f"  {py_file.relative_to(base_path)}: {lines} lines")
        except Exception as e:
            print(f"  {py_file.relative_to(base_path)}: Error reading file")
    
    print(f"\n📈 Total: {total_files} files, {total_lines} lines of code")

if __name__ == "__main__":
    print("🚀 TBG RAG Backend Structure Test")
    print("=" * 50)
    
    all_good = True
    
    # Test file structure
    all_good &= test_file_structure()
    
    # Test Python syntax  
    all_good &= test_python_syntax()
    
    # Count lines of code
    count_lines_of_code()
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All tests passed! Backend structure is ready.")
        print("💡 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Set up environment: cp .env.example .env")
        print("   3. Configure Supabase credentials in .env")
        print("   4. Run the server: python -m app.main")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)