install: 
	sudo python setup.py install

mtest: install
	python test/test.py
