import datetime

from django.db import models


class CategoryManager(models.Manager):

    def get_or_create(self, **kwargs) -> models.Model:
        result = self.filter(**kwargs)
        if len(result) == 0:
            return self.create(**kwargs)
        return result[0]


class EventManager(models.Manager):

    def get_or_create(
            self,
            teams: list[str],
            date: datetime.datetime,
            tournament: models.Model,
            parimatch_link: str | None = None
    ) -> models.Model:
        name = ' vs '.join(teams)
        filters = {'name': name, 'tournament': tournament}
        if parimatch_link:
            filters['parimatch_link'] = parimatch_link
        objects = self.filter(**filters)
        if len(objects) == 0:
            return self.create(**filters, start_time=date)
        return objects[0]


class TeamManager(models.Manager):

    def get_or_create(self, **kwargs) -> models.Model:
        result = self.filter(**kwargs)
        if len(result) == 0:
            return self.create(**kwargs)
        return result[0]


class DefaultManager(models.Manager):
    pass
