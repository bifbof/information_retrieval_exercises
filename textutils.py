# for stripping punctuation
# cf. https://stackoverflow.com/a/34294398
def remove_punctuation(s):
    import string

    trans = str.maketrans("", "", string.punctuation)
    return s.translate(trans)


# From book, figure 2.5
stop_words = [
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
]


def tokenize_document(doc):
    """
    Simple tokenizer for a single document referred to by a file name.
    To keep it efficient we implement the tokenizer as a python generator.
    """
    with open(doc, encoding="utf8") as d:
        for line in d:
            words = line.strip().split()
            for w in words:
                if w in stop_words:
                    continue
                yield remove_punctuation(w)


def remove_stop_words(query):
    """
    Remove stop words from a query string. This method will also tokenize
    `query` if it is not a list yet.
    """
    if isinstance(query, str):
        query = query.split(" ")
    assert isinstance(query, list)
    return list(filter(lambda w: w not in stop_words, query))


if __name__ == "__main__":
    print(remove_punctuation("flower”"))
