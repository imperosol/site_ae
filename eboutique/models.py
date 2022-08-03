import math

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from eboutique.exceptions import OverdraftError, BankLimitError
from site_ae.settings import BASE_DIR
from site_ae.settings import MAX_MONEY_ON_ACCOUNT


# Create your models here.

class ProductGroup(models.Model):
    """
    Modèle représentant une catégorie de produits.
    Dans la pratique, il sert surtout à définir les droits d'accès aux différents produits
    en fonction de l'utilisateur et de l'endroit où il se trouve (les mêmes produits ne seront pas disponibles
    au foyer et en ligne).
    """
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Modèle représentant un produit.
    Attention, ce modèle est abstrait et ne représente pas des objets réels.
    Pour représenter des produits vendus, utilisez la classe BasketItem (vente non-achevée) et la classe
    SoldItem (vente confirmée).

    Attributs :
        - name (str): Nom du produit.
        - price (int): Prix du produit en centimes.
        - category (ProductGroup): Catégorie du produit.
        - image (str): Chemin vers l'image du produit.
        - description (str): Brève description du produit.
        - is_available (bool): Indique si le produit est disponible ou non.
    """
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField()
    image = models.ImageField(upload_to=BASE_DIR / 'static/img/products', blank=True, null=True)
    category = models.ForeignKey(ProductGroup, related_name='products', on_delete=models.SET_NULL, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} : {self.price / 100:.2f}€"


class Discount(models.Model):
    """
    Modèle représentant une réduction sur un produit pour un nombre donné d'articles.
    Permet de représenter des réductions du type : "1€ l'un, 2€ les trois"
    """
    item = models.ForeignKey(Product, related_name='discount', on_delete=models.CASCADE)
    nbr_items = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('item', 'nbr_items')
        constraints = [CheckConstraint(check=Q(nbr_items__gt=1), name='au moins deux produits')]

    def save(self, *args, **kwargs):
        # on encadre la réduction pour qu'aucune réduction ne soit moins avantageuse
        # que le prix de base du produit
        original_price = self.item.price
        if self.price >= original_price * self.nbr_items:
            raise ValidationError("Une réduction ne peut être moins avantageuse que le produit original")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} : {self.price / 100:.2f}€ les {self.nbr_items}"


class Combination(models.Model):
    """
    Modèle représentant une combinaison de plusieurs produits formant un
    nouvel article avec un prix unique.
    Une combinaison peut regrouper des produits de catégories différentes.
    """
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField()
    image = models.ImageField(upload_to=BASE_DIR / 'static/img/products', blank=True, null=True)
    products = models.ManyToManyField(Product, related_name='combinations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} : {self.price / 100:.2f}€"


class Basket(models.Model):
    """
    Panier de l'utilisateur. Créé au cours de la commande et supprimé lorsque la commande est validée.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"panier de {self.user.username}"

    @property
    def total_price(self):
        items = self.basketitem_set.all()
        return sum(i.quantity * i.item.price for i in items)


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    item_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_type', 'item_id')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('basket', 'item_type', 'item_id')

    def __str__(self):
        return f"{self.item} - {self.quantity}"


class AccountRecharge(models.Model):
    """
    Modèle représentant une demande de rechargement de compte.
    """
    class Method(models.TextChoices):
        CASH = 'cash'
        CHEQUE = 'cheque'
        TRANSFER = 'transfer'
        GIFT = 'gift'
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    basket = models.OneToOneField(Basket, on_delete=models.CASCADE, null=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.TRANSFER)

    def __str__(self):
        return f"{self.user.username} - {self.amount}€"


class SoldItem(models.Model):
    """
    Modèle représentant un article vendu.

    L'attribut prix est redondant, mais il permet d'éviter de changer a posteriori
    le prix d'un article vendu en cas de changement du prix de vente du produit.
    """
    to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    item_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_type', 'item_id')
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField()
    date_sold = models.DateTimeField(auto_now_add=True)


    @classmethod
    def from_basket_item(cls, basket_item: BasketItem):
        return cls(
            to=basket_item.basket.user,
            item_type=ContentType.objects.get_for_model(basket_item.item),
            item_id=basket_item.item_id,
            quantity=basket_item.quantity,
            price=basket_item.item.price
        )

    def __str__(self):
        return f"{self.item}; to {self.to}; at {self.date_sold}"


class Balance(models.Model):
    """
    Modèle représentant le solde du compte AE d'un utilisateur.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # user can only have one money balance
    amount = models.PositiveBigIntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"solde de {self.user.username} : {self.amount / 100:.2f}€"

    def save(self, *args, **kwargs):
        if self.amount > MAX_MONEY_ON_ACCOUNT:
            raise BankLimitError(f"Vous pouvez pas dépasser le montant maximal de {MAX_MONEY_ON_ACCOUNT / 100:.2f}€")
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """
    Modèle représentant une transaction entre un utilisateur et l'AE.
    On y stocke le montant, la date de la transaction et l'utilisateur avec qui la transaction s'effectue.
    On y stocke aussi les numéros de comptes associés au débit et au crédit de l'opération comptable.
    Avant d'utiliser ce modèle, révisez vos bases de comptabilité !

    À chaque enregistrement d'une transaction, le solde de l'utilisateur est mis à jour
    si nécessaire. Si la mise à jour n'est pas possible (par exemple, si l'utilisateur se met en découvert),
    la transaction n'est pas enregistrée et une exception est levée.

    Attention ! Pour des raisons de précision, le montant de la transaction est en centimes.
    Pensez bien à multiplier par 100 pour obtenir le montant en euros.

    Voici quelques exemples d'opérations comptables qui peuvent être courantes :

        1. Un étudiant recharge son compte client de 20€. Dans ce cas, on crédite le compte 419 (client créditeur)
        et on débite le compte 512 (banque). Le couple de transaction s'écrit alors ainsi : ::

            user = request.user
            trans = Transaction(user=user, debit_account=512, credit_account=419, amount=2000)
            trans.save()

        2. Un étudiant achète pour 5€ un produit avec l'argent qu'il a précédemment placé sur son compte AE.
        Dans ce cas, on crédite le compte 707 (vente de marchandises) et on débite le compte 419.
        Le couple de transaction s'écrit alors ainsi : ::

            user = request.user
            trans = Transaction(user=user, debit_account=419, credit_account=707, amount=2000)
            trans.save()

        3. Un étudiant achète un produit pour 5€. Seulement, cette fois, il paie directement par carte bancaire
        depuis le site de l'AE. Dans ce cas, on crédite le compte 707 et on débite le compte 512.
        Le couple de transaction s'écrit alors ainsi : ::

            user = request.user
            trans = Transaction(user=user, debit_account=512, credit_account=707, amount=2000)
            trans.save()
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    amount = models.PositiveIntegerField()
    description = models.CharField(max_length=100, blank=True)
    debit_account = models.IntegerField(verbose_name='debit')  # compte débiteur
    credit_account = models.IntegerField(verbose_name='credit')  # compte créditeur

    def __str__(self):
        return f"transaction {self.date_created.replace(microsecond=0, tzinfo=None)}" \
               f" - {self.user.username} - {self.amount / 100:.2f}€"

    def save(self, *args, **kwargs):
        # On surcharge la méthode save pour modifier en même temps le solde de l'utilisateur.
        # Si la transaction met le solde en négatif, elle n'est pas autorisée.
        signed_amount = 0
        if self.credit_account == 419:  # compte client créditeur
            signed_amount = self.amount
        elif self.debit_account == 419:
            signed_amount = -self.amount
        if signed_amount != 0:
            balance, _ = Balance.objects.get_or_create(user=self.user)
            if balance.amount + signed_amount < 0:
                raise OverdraftError(f'Il ne vous reste que {balance.amount / 100:.2f}€')
            elif balance.amount + signed_amount > MAX_MONEY_ON_ACCOUNT:
                raise BankLimitError(f"Vous ne pouvez pas avoir plus de {MAX_MONEY_ON_ACCOUNT / 100:.2f}€")
            balance.amount += signed_amount
            balance.save()
        super().save(*args, **kwargs)
