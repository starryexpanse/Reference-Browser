
.PHONY: default
default: makedb

.PHONY: cleanthumbs
cleanthumbs:
	find . -name '*thumbnail*.png' | xargs rm
	find . -name '*thumbnail*.gif' | xargs rm
	rm -rf protected/images

.PHONY: cleangifs
cleangifs:
	find . -name '*.gif' | xargs rm

.PHONY: cleanmovies
cleanmovies:
	find . -name '*.m4v' | xargs rm

.PHONY: clean
clean: cleanthumbs

.PHONY: cleanall
cleanall: clean cleangifs cleanmovies

.PHONY: makedb
makedb:
	./makedb.py
