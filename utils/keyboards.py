from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)


def login_panel():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Login", callback_data="LOGIN")]])


def field_selection():
    return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("بلاک‌چین", callback_data="blockchain"),
                InlineKeyboardButton("نظریه‌بازی", callback_data="game_theory")
            ],
            [
                InlineKeyboardButton("ماشین خودران", callback_data="ai"),
                InlineKeyboardButton("شار", callback_data="algorithm")
            ],
            [
                InlineKeyboardButton("حرکت و گرانش", callback_data="gravity"),
                InlineKeyboardButton("کدینگ", callback_data="coding")
            ],
            [
                InlineKeyboardButton("✖️خروج✖️", callback_data="exit")
            ]
        ])


def countinue_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("➡️", callback_data="continue")]])


def answer_list(answers, max_row = 5):
    return InlineKeyboardMarkup([[InlineKeyboardButton(
            q["question"]["fileName"],
            callback_data=q["id"]
        )] for q in answers[:((max_row + 1) if len(answers) > max_row else len(answers))]])


def score(answer_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅", callback_data="1 " + answer_id),
        InlineKeyboardButton("❌", callback_data="0 " + answer_id)
    ]])