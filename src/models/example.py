from tortoise.models import Model
from tortoise import fields

class Example(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()

    def __str__(self):
        return self.name