# set some global vars
db = "log.db"
picture = 'Picture'
audio = 'Audio'
gif = 'GIF'
video = 'Video'
document = 'Document'
location = 'Location'
sticker = 'Sticker'
voice = 'Voice'
text = 'Text'


# shortcode list
def get_shortcode(w):
    return {
        '+': "{0} is in for it.",
        '-': "{0} send a classic 'Nope'.",
        '+!': "{0} is pretty hyped!",
        '+?': "{0} hopes he has time.",
        '-?': "{0} wants to come, but it's not looking good.",
        '+-': "{0} will be there, but only for a limited time.",
        '-+': "{0} will be late to the party."
    }.get(w, None)
