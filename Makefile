app_dir='browser'

.PHONY: default
default: makedb

.PHONY: cleanpositionthumbs
cleanpositionthumbs:
	find $(app_dir) -name '*thumbnail*.gif' | xargs rm

.PHONY: cleanthumbs
cleanthumbs: cleanpositionthumbs
	find $(app_dir) -name '*thumbnail*.png' | xargs rm
	rm -rf -- "$(app_dir)/protected/images"

.PHONY: cleangifs
cleangifs:
	find $(app_dir) -name '*.gif' | xargs rm

.PHONY: cleanmovies
cleanmovies:
	find $(app_dir) -name '*.m4v' | xargs rm

.PHONY: clean
clean: cleanthumbs

.PHONY: cleanall
cleanall: clean cleangifs cleanmovies

.PHONY: makedb
makedb:
	./makedb.py

.PHONY: run
run:
	python app.py

.PHONY: deploy
deploy:
	./deploy.sh
