push:
	git add .
	git commit -m "release"
	git push

build:
	rm -Rf ./dist
	uv build

install: 
	uv sync --all-groups
	uv sync --all-extras

update:
	copier update 