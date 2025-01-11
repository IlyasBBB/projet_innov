from django.contrib import admin
from .models import User, WasteContainer, WasteDeposit, Reward, RewardClaim, CollectionRecord

admin.site.register(User)
admin.site.register(WasteContainer)
admin.site.register(WasteDeposit)
admin.site.register(Reward)
admin.site.register(RewardClaim)
admin.site.register(CollectionRecord)
