#/***************************************************************************
# SGDiagramDownloader
#
# A tool for QGIS that will download SG (South African Surveyor General)
# diagrams.
#							 -------------------
#		begin				: 2014-05-30
#		copyright			: (C) 2014 by Kartoza (Pty) Ltd
#		email				: tim@kartoza.com
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################


#Add iso code for any locales you want to support here (space separated)
#LOCALES = en af de id
LOCALES = 

PLUGINNAME = SGDiagramDownloader

PY_FILES = \
	__init__.py \
	custom_logging.py \
	plugin.py \
	sg_downloader.py \
	sg_utilities.py \
	sg_action.py \
	sg_map_tool.py \
	database_manager.py \
	file_downloader.py \
	proxy.py \
	sg_exceptions.py \
	sg_log.py

EXTRAS = icon.png metadata.txt LICENSE README.md

STYLES = styles

#################################################
# Normally you would not need to edit below here
#################################################

HELP = 
#HELP = help/build/html

THIRD_PARTY = third_party

DATA_DIR = data

PLUGIN_UPLOAD = ./plugin_upload.py

QGISDIR=.qgis2

test: test_code pylint

test_code: # transcompile
	@echo
	@echo "----------------------"
	@echo "Regression Test Suite"
	@echo "----------------------"

	@# Preceding dash means that make will continue in case of errors
	@-export PYTHONPATH=`pwd`:`pwd`/third_party:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		nosetests -v --exclude pydev --with-id --with-coverage \
		--cover-package=. \
		3>&1 1>&2 2>&3 3>&- || true

#deploy: compile doc transcompile
deploy:
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)/python/plugins
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/i18n
	#cp -vfr i18n/*.qm $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/i18n/
	#cp -vfr $(HELP) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/help
	cp -vfr $(THIRD_PARTY) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/
	cp -vfr $(DATA_DIR) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/

fastdeploy: derase
	@echo
	@echo "------------------------------------------"
	@echo "Fast Deploying plugin to your .qgis2 directory."
	@echo "------------------------------------------"
	# The deploy  target only works on unix like operating system where
	# the Python plugin directory is located at:
	# $HOME/$(QGISDIR)/python/plugins
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/i18n
	cp -vfr $(THIRD_PARTY) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/
	cp -vfr $(DATA_DIR) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/

# The dclean target removes compiled python files from plugin directory
dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing any compiled python files."
	@echo "-----------------------------------"
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete

derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

zip: deploy dclean
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	# The zip target deploys the plugin and creates a zip file with the deployed
	# content. You can then upload the zip file on http://plugins.qgis.org
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins; zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

package: compile
	# Create a zip package of the plugin named $(PLUGINNAME).zip.
	# This requires use of git (your plugin development directory must be a
	# git repository).
	# To use, pass a valid commit or tag as follows:
	#   make package VERSION=Version_0.3.2
	@echo
	@echo "------------------------------------"
	@echo "Exporting plugin to zip package.	"
	@echo "------------------------------------"
	rm -f $(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	echo "Created package: $(PLUGINNAME).zip"

upload: zip
	@echo
	@echo "-------------------------------------"
	@echo "Uploading plugin to QGIS Plugin repo."
	@echo "-------------------------------------"
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiled translation files to .qm files."
	@echo "----------------------------------------"
	@scripts/compile-strings.sh $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

doc:
	@echo
	@echo "------------------------------------"
	@echo "Building documentation using sphinx."
	@echo "------------------------------------"
	#cd help; make clean; make html

tag:
	@echo
	@echo "------------------------------------"
	@echo "Tagging the release."
	@echo "------------------------------------"
	@# Note that make runs commands in a subshell so
	@# variable context is lost from one line to the next
	@# So we need to do everything as a single line command
	@read -p "Version e.g. 1.0.0: " VERSION; \
	    scripts/tag-release.sh $$VERSION

pylint:
	@echo
	@echo "-----------------"
	@echo "Pylint violations"
	@echo "-----------------"
	@pylint --reports=n --rcfile=pylintrc . | \
		grep -v locally-disabled || true


# Run flake8 style checking
flake8:
	@echo
	@echo "-----------"
	@echo "Flake8 issues"
	@echo "-----------"
	@flake8 --version
	@flake8 || true