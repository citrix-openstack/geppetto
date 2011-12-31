USE_BRANDING := yes
IMPORT_BRANDING := yes
ifdef B_BASE
include $(B_BASE)/common.mk
include $(B_BASE)/rpmbuild.mk
REPO := /repos/geppetto
HORIZON_UPSTREAM := /repos/horizon
OPENSTACKX_UPSTREAM := /repos/openstackx
else
REPO := .
HORIZON_UPSTREAM := ../horizon
OPENSTACKX_UPSTREAM := ../openstackx
endif


GEPPETTO_FULLNAME := citrix-geppetto-$(PRODUCT_VERSION)-$(BUILD_NUMBER)
GEPPETTO_BASE_FULLNAME := citrix-geppetto-base-$(PRODUCT_VERSION)-$(BUILD_NUMBER)
GEPPETTO_CLIENT_FULLNAME := citrix-geppetto-client-$(PRODUCT_VERSION)-$(BUILD_NUMBER)
GEPPETTO_MEDIA_FULLNAME := citrix-geppetto-media-$(PRODUCT_VERSION)-$(BUILD_NUMBER)
GEPPETTO_SPEC := $(MY_OBJ_DIR)/citrix-geppetto.spec
GEPPETTO_RPM_TMP_DIR := $(MY_OBJ_DIR)/RPM_BUILD_DIRECTORY/tmp/citrix-geppetto
GEPPETTO_RPM_TMP := $(MY_OBJ_DIR)/RPMS/noarch/$(GEPPETTO_FULLNAME).noarch.rpm
GEPPETTO_TARBALL := $(MY_OBJ_DIR)/SOURCES/$(GEPPETTO_FULLNAME).tar.gz
GEPPETTO_CLIENT_TARBALL := $(MY_OBJ_DIR)/SOURCES/$(GEPPETTO_CLIENT_FULLNAME).tar.gz
GEPPETTO_MEDIA_TARBALL := $(MY_OBJ_DIR)/SOURCES/$(GEPPETTO_MEDIA_FULLNAME).tar.gz
GEPPETTO_BASE_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/citrix-geppetto-base-$(PRODUCT_VERSION)-$(BUILD_NUMBER).noarch.rpm
GEPPETTO_CLIENT_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/citrix-geppetto-client-$(PRODUCT_VERSION)-$(BUILD_NUMBER).noarch.rpm
GEPPETTO_CONSOLE_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/citrix-geppetto-console-$(PRODUCT_VERSION)-$(BUILD_NUMBER).noarch.rpm
GEPPETTO_SERVER_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/citrix-geppetto-server-$(PRODUCT_VERSION)-$(BUILD_NUMBER).noarch.rpm
GEPPETTO_SRPM := $(MY_OUTPUT_DIR)/SRPMS/$(GEPPETTO_FULLNAME).src.rpm


DASHBOARD_VERSION := $(shell PYTHONPATH=$(HORIZON_UPSTREAM)/horizon \
                               python -c 'import horizon.version; print horizon.version.canonical_version_string()')

MY_DB_OBJ_DIR := $(MY_OBJ_DIR)/openstack-dashboard
DASHBOARD_FULLNAME := openstack-dashboard-$(DASHBOARD_VERSION)-$(BUILD_NUMBER)
DASHBOARD_MEDIA_FULLNAME := openstack-dashboard-media-$(DASHBOARD_VERSION)-$(BUILD_NUMBER)
DASHBOARD_SPEC := $(MY_DB_OBJ_DIR)/openstack-dashboard.spec
DASHBOARD_RPM_TMP_DIR := $(MY_DB_OBJ_DIR)/RPM_BUILD_DIRECTORY/tmp/openstack-dashboard
DASHBOARD_RPM_TMP := $(MY_DB_OBJ_DIR)/RPMS/noarch/$(DASHBOARD_FULLNAME).noarch.rpm
DASHBOARD_TARBALL := $(MY_DB_OBJ_DIR)/SOURCES/$(DASHBOARD_FULLNAME).tar.gz
DASHBOARD_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/$(DASHBOARD_FULLNAME).noarch.rpm
DASHBOARD_SRPM := $(MY_OUTPUT_DIR)/SRPMS/$(DASHBOARD_FULLNAME).src.rpm

OPENSTACKX_VERSION := 1.0
OPENSTACKX_OBJ_DIR := $(MY_OBJ_DIR)/openstackx
OPENSTACKX_FULLNAME := openstackx-$(OPENSTACKX_VERSION)-$(BUILD_NUMBER)
OPENSTACKX_SPEC := $(OPENSTACKX_OBJ_DIR)/openstackx.spec
OPENSTACKX_RPM_TMP_DIR := $(OPENSTACKX_OBJ_DIR)/RPM_BUILD_DIRECTORY/tmp/openstackx
OPENSTACKX_RPM_TMP := $(OPENSTACKX_OBJ_DIR)/RPMS/noarch/$(OPENSTACKX_FULLNAME).noarch.rpm
OPENSTACKX_TARBALL := $(OPENSTACKX_OBJ_DIR)/SOURCES/$(OPENSTACKX_FULLNAME).tar.gz
OPENSTACKX_RPM := $(MY_OUTPUT_DIR)/RPMS/noarch/$(OPENSTACKX_FULLNAME).noarch.rpm
OPENSTACKX_SRPM := $(MY_OUTPUT_DIR)/SRPMS/$(OPENSTACKX_FULLNAME).src.rpm

EPEL_RPM_DIR := $(CARBON_DISTFILES)/epel5
EPEL_YUM_DIR := $(MY_OBJ_DIR)/epel5

EPEL_REPOMD_XML := $(EPEL_YUM_DIR)/repodata/repomd.xml
REPOMD_XML := $(MY_OUTPUT_DIR)/repodata/repomd.xml

RPMS := $(GEPPETTO_BASE_RPM) $(GEPPETTO_CLIENT_RPM) $(GEPPETTO_CONSOLE_RPM) $(GEPPETTO_SERVER_RPM) $(GEPPETTO_SRPM) \
	$(OPENSTACKX_SRPM) $(OPENSTACKX_RPM) \
	$(DASHBOARD_SRPM) $(DASHBOARD_RPM)

OUTPUT := $(RPMS) $(REPOMD_XML)

# Disable idiotic predefined implicit rule that wants to overwrite
# openstack-dashboard with the contents of openstack-dashboard.sh.
%: %.sh

.PHONY: build
build: $(OUTPUT)

$(GEPPETTO_SRPM): $(GEPPETTO_CONSOLE_RPM)
$(GEPPETTO_BASE_RPM): $(GEPPETTO_CONSOLE_RPM)
$(GEPPETTO_SERVER_RPM): $(GEPPETTO_CONSOLE_RPM)
$(GEPPETTO_CLIENT_RPM): $(GEPPETTO_CONSOLE_RPM)
$(GEPPETTO_CONSOLE_RPM): $(GEPPETTO_SPEC) $(GEPPETTO_TARBALL) $(GEPPETTO_CLIENT_TARBALL) $(GEPPETTO_MEDIA_TARBALL) $(EPEL_REPOMD_XML) \
	     $(shell find $(REPO)/citrix-geppetto -type f)
	cp -f $(REPO)/citrix-geppetto/* $(MY_OBJ_DIR)/SOURCES
	cp -f $(shell find $(REPO)/puppet/ -type f -name "*") $(MY_OBJ_DIR)/SOURCES
	cp -f $(shell find $(REPO)/scripts/ -type f -name "*") $(MY_OBJ_DIR)/SOURCES
	sh build-geppetto.sh $@ $< $(MY_OBJ_DIR)/SOURCES

$(DASHBOARD_SRPM): $(DASHBOARD_RPM)
$(DASHBOARD_RPM): $(DASHBOARD_SPEC) $(DASHBOARD_TARBALL) $(EPEL_REPOMD_XML) \
	     $(shell find $(REPO)/openstack-dashboard -type f)
	cp -f $(REPO)/openstack-dashboard/* $(MY_DB_OBJ_DIR)/SOURCES
	sh build-geppetto.sh $@ $< $(MY_DB_OBJ_DIR)/SOURCES

$(OPENSTACKX_SRPM): $(OPENSTACKX_RPM)
$(OPENSTACKX_RPM): $(OPENSTACKX_SPEC) $(OPENSTACKX_TARBALL) $(EPEL_REPOMD_XML)
	sh build-geppetto.sh $@ $< $(OPENSTACKX_OBJ_DIR)/SOURCES

$(MY_OBJ_DIR)/%.spec: $(REPO)/citrix-geppetto/%.spec.in
	mkdir -p $(dir $@)
	$(call brand,$^) >$@

$(MY_DB_OBJ_DIR)/%.spec: $(REPO)/openstack-dashboard/openstack-dashboard.spec.in
	mkdir -p $(dir $@)
	$(call brand,$^) >$@
	sed -e 's,@DASHBOARD_VERSION@,$(DASHBOARD_VERSION),g' -i $@

$(OPENSTACKX_OBJ_DIR)/%.spec: $(REPO)/openstackx/openstackx.spec.in
	mkdir -p $(dir $@)
	$(call brand,$^) >$@
	sed -e 's,@OPENSTACKX_VERSION@,$(OPENSTACKX_VERSION),g' -i $@

$(GEPPETTO_TARBALL): $(shell find $(REPO)/os-vpx-mgmt -type f)
	rm -rf $@ $(MY_OBJ_DIR)/citrix-geppetto-$(PRODUCT_VERSION)
	mkdir -p $(@D)
	cp -a $(REPO)/os-vpx-mgmt $(MY_OBJ_DIR)/citrix-geppetto-$(PRODUCT_VERSION)
	tar -C $(MY_OBJ_DIR) -czf $@ citrix-geppetto-$(PRODUCT_VERSION)

$(GEPPETTO_CLIENT_TARBALL): $(shell find $(REPO)/os-vpx-scripts -type f)
	rm -rf $@ $(MY_OBJ_DIR)/citrix-geppetto-client-$(PRODUCT_VERSION)
	mkdir -p $(@D)
	cp -a $(REPO)/os-vpx-scripts $(MY_OBJ_DIR)/citrix-geppetto-client-$(PRODUCT_VERSION)
	tar -C $(MY_OBJ_DIR)/citrix-geppetto-client-$(PRODUCT_VERSION) -czf $@ usr

$(DASHBOARD_TARBALL): $(shell find $(HORIZON_UPSTREAM) -type f)
	rm -rf $@ $(MY_DB_OBJ_DIR)/openstack-dashboard-$(DASHBOARD_VERSION)
	mkdir -p $(@D)
	cp -a $(HORIZON_UPSTREAM) $(MY_DB_OBJ_DIR)/openstack-dashboard-$(DASHBOARD_VERSION)
	tar -C $(MY_DB_OBJ_DIR) -czf $@ openstack-dashboard-$(DASHBOARD_VERSION)

$(GEPPETTO_MEDIA_TARBALL): $(shell find $(REPO)/os-vpx-mgmt/geppetto-media -type f)
	rm -rf $@ $(MY_OBJ_DIR)/citrix-geppetto-media-$(PRODUCT_VERSION)
	mkdir -p $(@D)
	cp -a $(REPO)/os-vpx-mgmt/geppetto-media $(MY_OBJ_DIR)/citrix-geppetto-media-$(PRODUCT_VERSION)
	tar -C $(MY_OBJ_DIR) -czf $@ citrix-geppetto-media-$(PRODUCT_VERSION)

$(OPENSTACKX_TARBALL): $(shell find $(REPO)/openstackx -type f)
	rm -rf $@ $(OPENSTACKX_OBJ_DIR)/$(OPENSTACKX_FULLNAME)
	mkdir -p $(@D)
	mkdir -p $(OPENSTACKX_OBJ_DIR)/$(OPENSTACKX_FULLNAME)
	cp -a $(OPENSTACKX_UPSTREAM) $(OPENSTACKX_OBJ_DIR)/$(OPENSTACKX_FULLNAME)
	tar -C $(OPENSTACKX_OBJ_DIR) -czf $@ $(OPENSTACKX_FULLNAME)

$(REPOMD_XML): $(RPMS)
	createrepo $(MY_OUTPUT_DIR)

$(EPEL_REPOMD_XML): $(wildcard $(EPEL_RPM_DIR)/%)
	$(call mkdir_clean,$(EPEL_YUM_DIR))
	cp -s $(EPEL_RPM_DIR)/* $(EPEL_YUM_DIR)
	createrepo $(EPEL_YUM_DIR)

.PHONY: clean
clean:
	rm -f $(OUTPUT)
	rm -rf $(MY_OBJ_DIR)/*
