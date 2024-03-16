from django.contrib import admin

from app.models import CustomUser, Story, Transaction, Referral, OTP


admin.site.register(CustomUser)
admin.site.register(Story)
admin.site.register(Transaction)
admin.site.register(Referral)
admin.site.register(OTP)
