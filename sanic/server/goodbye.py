import sys, random

# fmt: off
ascii_phrases = {
    'Farewell', 'Bye', 'See you later', 'Take care', 'So long', 'Adieu', 'Cheerio',
    'Goodbye', 'Adios', 'Au revoir', 'Arrivederci', 'Sayonara', 'Auf Wiedersehen',
    'Do svidaniya', 'Annyeong', 'Tot ziens', 'Ha det', 'Selamat tinggal',
    'Hasta luego', 'Nos vemos', 'Salut', 'Ciao', 'A presto',
    'Dag', 'Tot later', 'Vi ses', 'Adjø', 'Sampai jumpa', 'Dadah'
}

non_ascii_phrases = {
    'Tschüss', 'Zài jiàn', 'Bāi bāi', 'Míngtiān jiàn', 'Adeus', 'Tchau', 'Até logo',
    'Hejdå', 'À bientôt', 'Bis später', 
    'じゃね', 'またね', '안녕히 계세요', '안녕히 가세요', '잘 가', 'שלום',
    'להתראות', 'נתראה', 'مع السلامة', 'إلى اللقاء', 'وداعاً', 'अलविदा',
    'फिर मिलेंगे', 'नमस्ते'
}

all_phrases = ascii_phrases | non_ascii_phrases
# fmt: on


def get_goodbye() -> str:  # pragma: no cover
    is_utf8 = sys.stdout.encoding.lower() == "utf-8"
    phrases = all_phrases if is_utf8 else ascii_phrases
    return random.choice(list(phrases))
