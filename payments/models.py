import random
import uuid
import string

from pyqiwip2p import QiwiP2P
from pyqiwip2p.types import Bill
from django.db import models
from multipledispatch import dispatch

from . import config
from . import managers
from data.models import TGUser


p2p = QiwiP2P(auth_key=config.QIWI_PRIV_KEY)


class Product(models.Model):
    class Meta:
        verbose_name_plural = 'Продукты'

    name = models.CharField(max_length=25, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    amount = models.IntegerField(verbose_name="Стоимость")


class Cheque(models.Model):
    class Meta:
        verbose_name_plural = "Ставки"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='ID')
    user = models.ForeignKey(TGUser, on_delete=models.CASCADE, verbose_name='Покупатель')
    status = models.BooleanField(default=False, verbose_name='Оплата')
    canceled = models.BooleanField(default=False, verbose_name='Отменён')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='cheques', verbose_name='Продукт')
    bill_id = models.CharField(max_length=10, verbose_name='BillID')
    url = models.URLField(verbose_name="Ссылка на оплату", null=True, default='')

    objects = managers.DefaultManager()

    class DoesNotAccess(Exception):
        description: str

        def __init__(self, description: str = None):
            if description is None:
                description = "Комментарий отсутствует"
            self.description = description

        def __str__(self):
            return f"Отказано в доступе.\nПодробнее: {self.description}"

    @classmethod
    def create(cls, user: TGUser, product: Product, time: int = 900) -> "Cheque":
        """
        Метод для выставления счета.

        :param product: Product object
        :type product: Product
        :param user: Telegram user object
        :type user: TGUser
        :param time: Cheque lifetime
        :type time: int
        :return: Cheque
        """
        if not user.status:
            raise cls.DoesNotAccess("Ваш аккаунт имеет блокировку")
        letters = string.ascii_lowercase
        bill_id = ''.join(random.choice(letters) for i in range(20))
        new_bill: Bill = p2p.bill(bill_id=bill_id, amount=1, lifetime=time)
        return cls.objects.create(user=user, product=product, bill_id=new_bill.bill_id, url=new_bill.pay_url)

    @dispatch(TGUser)
    def check(self, user: TGUser):
        if self.status:
            return True
        if self.canceled:
            return False
        bill: Bill = p2p.check(bill_id=self.bill_id)
        if bill.status == "PAID":
            self.status = True
            self.save()
            return True
        return False

    @classmethod
    @dispatch(TGUser, int)
    def check(cls, user: TGUser, cheque_id: int) -> bool:
        try:
            cheque = cls.objects.get(user=user, id=cheque_id)
            return cheque.check()
        except cls.DoesNotExist:
            raise cls.DoesNotAccess("Указаного чека не обнаружено в базе данных")

    @classmethod
    @dispatch(TGUser, list)
    def check(cls, user: TGUser, cheque_ids: list[int]) -> list[bool]:
        bill_statuses: list[bool] = []
        for cheque_id in cheque_ids:
            bill_statuses.append(cls.check(user, cheque_id))
        return bill_statuses

    @classmethod
    @dispatch(TGUser)
    def check(cls, user: TGUser) -> list[bool]:
        bill_statuses: list[bool] = []
        for cheque in cls.objects.filter(user=user):
            bill_statuses.append(cheque.check())
        return bill_statuses

    def cancel(self):
        if self.check():
            return False
        p2p.reject(bill_id=self.bill_id)
        self.canceled = True
        self.save()
        return True
