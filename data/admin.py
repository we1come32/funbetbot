from django.contrib import admin
from . import models


@admin.register(models.TGUser)
class TGUserModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", 'balance')
    list_filter = ("admin",)
    search_fields = ("id", "name",)
    fieldsets = (
        (None, {
            'fields': ('status', 'admin', 'balance')
        }),
        ('Внутренние параметры', {
            'classes': ('collapse',),
            'fields': ('id', 'name', 'language', 'tg_language'),
        }),
    )


@admin.register(models.Category)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    search_fields = ("name",)

    @staticmethod
    def count_of(a):
        return a.subcategories.all().count()


@admin.register(models.SubCategory)
class SubCategoryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    list_filter = ("category",)
    search_fields = ("name",)

    @staticmethod
    def count_of(a):
        return a.tournaments.all().count()


@admin.register(models.Tournament)
class TournamentModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    list_filter = ("subcategory__category", 'subcategory',)
    search_fields = ("name",)

    @staticmethod
    def count_of(a):
        return a.events.all().count()


@admin.register(models.Event)
class EventModelAdmin(admin.ModelAdmin):
    list_display = ("name", 'pm_link', 'sports_link', 'not_supported', "tournament", "ended", 'start_time', )
    list_filter = ("not_supported", "tournament__subcategory__category",
                   'tournament__subcategory', "tournament", "ended",)
    search_fields = ("name", "tournament__name",)
    fieldsets = (
        (None, {
            'fields': ('name', 'tournament', 'start_time', 'ended', 'not_supported')
        }),
        ('Внутренние параметры', {
            'classes': ('collapse',),
            'fields': ('parimatch_link', 'sports_ru_link'),
        }),
    )

    @staticmethod
    def pm_link(a):
        return a.parimatch_link != ''

    @staticmethod
    def sports_link(a):
        return a.sports_ru_link != ''


@admin.register(models.TeamEvent)
class TeamModelAdmin(admin.ModelAdmin):
    list_display = ("team",)
    search_fields = ("team__parimatch_name","team__sports_name",)


@admin.register(models.Bet)
class BetModelAdmin(admin.ModelAdmin):
    list_display = ("user", "win_money", "is_active_status")
    list_filter = ("team__event", )
    search_fields = ("user__id", "user__name__startswith",)
    fieldsets = (
        (None, {
            'fields': ('user', 'win_money', 'is_active_status')
        }),
        ('Внутренние параметры', {
            'classes': ('collapse',),
            'fields': ('value', 'money'),
        }),
    )

    @staticmethod
    def win_money(self):
        return self.money * self.value

    @staticmethod
    def is_active_status(self):
        return self.is_active and not self.payed
