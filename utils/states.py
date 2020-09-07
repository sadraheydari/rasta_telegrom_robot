from telegram.ext import ConversationHandler


START, GET_USERNAME, GET_PASSWORD, LOGIN, SELECT_FIELD, SELECT_Q, SCORE_Q = range(7)
END = ConversationHandler.END