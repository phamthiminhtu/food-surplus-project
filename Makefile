VENV := $(HOME)/workspace/env-food-surplus-project
PYTHON := source $(VENV)/bin/activate &&

.PHONY: run test-ocr install

run:
	$(PYTHON) streamlit run app.py

test-ocr:
	$(PYTHON) python -c "\
import sys, os; sys.path.insert(0, 'src'); \
from ocr import OcrReader; \
reader = OcrReader(); \
[print(f + ':', repr(reader.extract_text(open('data/images/' + f, 'rb').read())[:80]) or '(empty)') \
 for f in sorted(os.listdir('data/images')) \
 if not f.startswith('.') and f.lower().endswith(('.png', '.jpg', '.jpeg'))]"

install:
	uv pip install -r requirements.txt --python $(VENV)/bin/python
