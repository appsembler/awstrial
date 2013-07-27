#    AWSTrial, A mechanism and service for offering a cloud image trial
#
#    Copyright (C) 2010  Scott Moser <smoser@ubuntu.com>
#    Copyright (C) 2010  Dave Walker (Daviey) <DaveWalker@ubuntu.com>
#    Copyright (C) 2010  Michael Hall <mhall119@gmail.com>
#    Copyright (C) 2010  Dustin Kirkland <kirkland@ubuntu.com>
#    Copyright (C) 2010  Andreas Hasenack <andreas@canonical.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.forms import ModelForm
from django import forms
from django.contrib import admin
from trial.models import Campaign, Instances, Feedback, UserProfile, EmailBlacklist, GmailAlias


class UsernameUserAdminForm(ModelForm):
    username = forms.CharField()
    class Meta:
         model = User 


class UsernameUserAdmin(UserAdmin):
    form = UsernameUserAdminForm


admin.site.unregister(User) 
admin.site.register(User, UsernameUserAdmin)  


class CampaignAdmin(admin.ModelAdmin):
    pass


class InstancesAdmin(admin.ModelAdmin):
    list_display = ('instance_id','owner','campaign','running_time','status','ip')
    search_fields = ('owner__username','instance_id','ip')
    list_filter = ['campaign', 'reservation_time']
    date_hierarchy = "reservation_time"


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user','email', 'inst_links')

    def email(self, feedback):
        return(feedback.user.email)

    def inst_links(self, feedback):
        rset = Instances.objects.filter(owner=feedback.user)
        if rset.count() == 0: return ""
        links= []
        for i in rset:
           links.append("<a href='../instances/%s/'>%s</a>" %
               (str(i.id), i.instance_id))
        return(','.join(links))
    inst_links.allow_tags = True


class UserProfileAdmin(admin.ModelAdmin):
    pass


class EmailBlacklistAdmin(admin.ModelAdmin):
    pass

class GmailAliasAdmin(admin.ModelAdmin):
    pass


admin.site.unregister(User) 
admin.site.register(User, UsernameUserAdmin)  
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Instances, InstancesAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EmailBlacklist, EmailBlacklistAdmin)
admin.site.register(GmailAlias, GmailAliasAdmin)
