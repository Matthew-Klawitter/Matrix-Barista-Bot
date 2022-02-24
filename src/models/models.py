from tortoise.models import Model
from tortoise import fields

class Example(Model):
    id = fields.IntField(pk=True)
    text = fields.TextField()

    def __str__(self) -> str:
        return self.text