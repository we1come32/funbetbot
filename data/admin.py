from django.contrib import admin
from . import models


@admin.register(models.TGUser)
class TGUserModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", 'balance', 'get_bets',)
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

    @admin.display(description='Кол-во ставок')
    def get_bets(self, a) -> int:
        return a.bets.filter(is_active=True, payed=False).count()


@admin.register(models.Category)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    search_fields = ("name",)

    @admin.display(description="Количество категорий", ordering=True)
    def count_of(self, a):
        return a.subcategories.all().count()


@admin.register(models.SubCategory)
class SubCategoryModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    list_filter = ("category",)
    search_fields = ("name",)

    @admin.display(description="Количество турниров", ordering=True)
    def count_of(self, a):
        return a.tournaments.all().count()


@admin.register(models.Tournament)
class TournamentModelAdmin(admin.ModelAdmin):
    list_display = ("name", "count_of",)
    list_filter = ("subcategory__category", 'subcategory',)
    search_fields = ("name",)

    @admin.display(description="Количество событий", ordering=True)
    def count_of(self, a):
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

    @admin.display(description="PM", boolean=True)
    def pm_link(self, obj):
        return obj.parimatch_link != ''

    @admin.display(description="SP", boolean=True)
    def sports_link(self, obj):
        return obj.sports_ru_link != ''


@admin.register(models.TeamEvent)
class TeamEventModelAdmin(admin.ModelAdmin):
    list_display = ("team",)
    search_fields = ("team__parimatch_name","team__sports_name",)


@admin.register(models.Bet)
class BetModelAdmin(admin.ModelAdmin):
    list_display = ("get_id", "user", "team", "win_money", "is_active_status")
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
