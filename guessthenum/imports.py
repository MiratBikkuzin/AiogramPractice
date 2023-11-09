from config import BOT_TOKEN
from for_db.db_connection import CONNECTION
from for_db.db_queries import *
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from random import randint
import re