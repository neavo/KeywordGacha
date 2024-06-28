@echo off

	pip install --upgrade janome

	pip install --upgrade setuptools wheel
	pip install --upgrade spacy
	python -m spacy download ja_core_news_lg

	pip install --upgrade sudachipy
	pip install --upgrade sudachidict_small
	pip install --upgrade sudachidict_core
	pip install --upgrade sudachidict_full

pause