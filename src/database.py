import os

from tortoise import Tortoise

TORTOISE_ORM = {
    "connections": {
         "default": os.getenv("DB_CONNECTION_STRING")
    },
    "apps": {
        "app": {
            "models": [
                 "models.example", "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}

TORTOISE_ORM_DEPLOY = {
    "connections": {
         "default": os.getenv("DB_CONNECTION_STRING")
    },
    "apps": {
        "app": {
            "models": [
                 "models.example"
            ],
            "default_connection": "default",
        },
    },
}

async def init_db():
    await Tortoise.init(TORTOISE_ORM_DEPLOY)