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
    list_display = ("name", 'pm_link', 'sports_link', "tournament", "ended", 'start_time', )
    list_filter = ("tournament__subcategory__category",
                   'tournament__subcategory', "tournament", "ended",)
    search_fields = ("name", "tournament__name",)
    fieldsets = (
        (None, {
            'fields': ('name', 'tournament', 'start_time', 'ended')
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
class TeamEventModelAdmin(admin.ModelAdmin):
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


@admin.register(models.Team)
class TeamModelAdmin(admin.ModelAdmin):
    list_display = ("pk", "get_main", "get_names", 'appl')
    search_fields = ("names__name__contains",)

    @staticmethod
    def get_main(self):
        return self.names.get(primary=True).name

    @staticmethod
    def appl(model):
        return ', '.join(f"{_.name!r}" for _ in model.names.filter(verified=False, denied=False))

    @staticmethod
    def get_names(model):
        return ', '.join(f"{_.name!r}" for _ in model.names.filter(verified=True))


@admin.register(models.TeamName)
class TeamNameModelAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "team", 'verified', 'primary')
    list_filter = ("verified", 'denied', "primary",)
    search_fields = ("name",)
