from django.contrib import admin
from django.conf.urls.defaults import *

from cumulus.models import Account
from cumulus.views import *

class AccountAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(AccountAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(?P<account_id>[\d]+)/cloud-files/$',
                self.admin_site.admin_view(edit_cloudfiles),
                name='cumulus-edit-cloudfiles'),
            url(r'^(?P<account_id>[\d]+)/cloud-files/create/$',
                self.admin_site.admin_view(create_container),
                name='cumulus-create-container'),
            url(r'^(?P<account_id>[\d]+)/cloud-files/(?P<container_name>.+)/upload/$',
                self.admin_site.admin_view(upload_file),
                name='cumulus-upload-file'),
            url(r'^(?P<account_id>[\d]+)/cloud-files/(?P<container_name>.+)/objects/$',
                self.admin_site.admin_view(container_objects),
                name='cumulus-container-objects'),
            url(r'^(?P<account_id>[\d]+)/cloud-files/(?P<container_name>.+)/$',
                self.admin_site.admin_view(container_info),
                name='cumulus-container-info'),
        )
        return my_urls + urls
    
    list_display = ('username', 'api_key', 'manage_cloudfiles')

admin.site.register(Account, AccountAdmin)