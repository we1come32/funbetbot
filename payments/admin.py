from django.contrib import admin
from . import models


@admin.register(models.Product)
class Product(admin.ModelAdmin):
    list_display = ("name", "amount", "count_of",)
    search_fields = ("name__startswitch",)

    @admin.display(description="Оплаченные чеки")
    def get_id(self, obj):
        return obj.cheques.filter(canceled=False)

    @admin.display(description="Оплаченные чеки")
    def get_id(self, obj):
        return obj.cheques.filter(canceled=False)


@admin.register(models.Cheque)
class Cheque(admin.ModelAdmin):
    list_display = ("id", "user", "status", "canceled", "is_active_status", 'winner',)
    list_filter = ("team__event__tournament", "team__event",)
    search_fields = ("user__id", "user__name__startswith",)
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Внутренние параметры', {
            'classes': ('collapse',),
            'fields': ('value', 'money'),
        }),
    )

    @admin.display(description="ID")
    def get_id(self, obj):
        return obj.pk

    @admin.display(description="Выигрыш")
    def win_money(self, obj):
        return int(obj.money * obj.value)

    @admin.display(description="Статус", boolean=True)
    def is_active_status(self, obj):
        return obj.is_active and not obj.payed