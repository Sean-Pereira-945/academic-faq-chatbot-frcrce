#!/usr/bin/env python3
"""
Setup Verification Script for Academic FAQ Chatbot
Tests that all dependencies are properly installed and accessible.
"""

import sys
import importlib
import io
from contextlib import redirect_stdout
from unittest import mock

import test_setup

def check_import(module_name, friendly_name=None):
    """Test if a module can be imported successfully."""
    if friendly_name is None:
        friendly_name = module_name
    
    try:
        if module_name == "sentence_transformers":
            try:
                import semantic_search  # noqa: F401  # Ensure compatibility shim is registered
            except Exception as compat_exc:  # pragma: no cover - best-effort shim
                print(f"Warning: Sentence Transformers compatibility shim warning: {compat_exc}")
        importlib.import_module(module_name)
        print(f"{friendly_name} - Successfully imported")
        return True
    except ImportError as e:
        print(f"{friendly_name} - Import failed: {e}")
        return False

def main():
    """Run all setup verification tests."""
    print("Academic FAQ Chatbot - Setup Verification")
    print("=" * 50)
    
    # Test Python version
    print(f"Python Version: {sys.version}")
    print()
    
    # Test core dependencies
    dependencies = [
        ("sentence_transformers", "Sentence Transformers"),
        ("faiss", "FAISS"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("PyPDF2", "PyPDF2"),
        ("bs4", "BeautifulSoup4"),
        ("requests", "Requests"),
        ("streamlit", "Streamlit")
    ]
    
    success_count = 0
    total_count = len(dependencies)
    
    for module, name in dependencies:
        if check_import(module, name):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Setup Verification Results: {success_count}/{total_count} dependencies working")
    
    if success_count == total_count:
        print("All dependencies installed successfully!")
        print("Ready to proceed to Phase 2!")
    else:
        print("Some dependencies failed. Please reinstall missing packages.")
        
    # Test folder structure
    import os
    required_folders = ['data', 'data/pdfs', 'data/web_pages', 'models', 'tests', 'docs']
    print("\nFolder Structure Check:")
    
    for folder in required_folders:
        if os.path.exists(folder):
            print(f"{folder}/ - exists")
        else:
            print(f"{folder}/ - missing")

def test_test_import_success():
    with mock.patch.object(importlib, "import_module", return_value=None):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = test_setup.check_import("pkg", "Pkg")
    assert result is True
    assert "Pkg - Successfully imported" in buffer.getvalue()


def test_test_import_failure():
    with mock.patch.object(importlib, "import_module", side_effect=ImportError("boom")):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = test_setup.check_import("pkg", "Pkg")
    assert result is False
    assert "Pkg - Import failed: boom" in buffer.getvalue()


def test_main_reports_partial_success():
    real_import_module = importlib.import_module

    def fake_import(name):
        if name == "pandas":
            raise ImportError("pandas missing")
        return real_import_module(name)

    with mock.patch.object(importlib, "import_module", side_effect=fake_import):
        with mock.patch("os.path.exists", return_value=True):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                test_setup.main()
    output = buffer.getvalue()
    assert "Setup Verification Results: 7/8 dependencies working" in output
    assert "Pandas - Import failed" in output

if __name__ == "__main__":
    main()