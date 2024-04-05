import pytest
import random
import string
from Levenshtein import distance
from math import floor, sqrt


@pytest.fixture
def random_substitution():
    def func(word):
        if len(word) == 0:
            return word

        pos = random.randint(0, len(word) - 1)
        return "word"[:pos] + random.choice(string.ascii_letters) + word[pos + 1 :]

    return func


@pytest.fixture
def random_insertion():
    def func(word):
        pos = random.randint(0, len(word))
        return word[:pos] + random.choice(string.ascii_letters) + word[pos:]

    return func


@pytest.fixture
def random_deletion():
    def func(word):
        if len(word) == 0:
            return word

        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos + 1 :]

    return func


@pytest.fixture
def base_words():
    return [
        "A",
        "C",
        "Olivier",
        "Oliver",
        "Oli",
        "banana",
        "tomato",
        "extravagant",
        "dog",
        "cat",
        "test",
        "potato",
        "mail",
        "computer",
        "tv",
        "television",
    ]


@pytest.fixture
def noisy_base_words(
    base_words, random_substitution, random_insertion, random_deletion
):
    def func(n):
        dictionary = set()
        for word in base_words:
            dictionary.add(word)
            for i in range(n):
                for _ in range(i):
                    func = random.choice(
                        [random_substitution, random_insertion, random_deletion]
                    )
                    dictionary.add(func(word))

        return dictionary

    return func


@pytest.fixture
def trie_search_oracle():
    def func(trie, query, n):
        query = trie.preprocess(query)
        matching_set, visited, stack = set(), set(), [trie.root]
        while stack:
            node = stack.pop()
            if node not in visited:
                if node.is_word:
                    if distance(node.word, query) <= n:
                        matching_set.add(node.word)
                stack.extend(node.children.values())
        return matching_set

    return func


@pytest.fixture
def index_search_oracle(trie_search_oracle):
    def func(index, query, n):
        matching_set = trie_search_oracle(index.trie, query, n)
        return {doc for word in matching_set for doc in index.inverted_index[word]}

    return func


def test_fuzzy_search_smoke():
    from simplesearch import Trie

    trie = Trie()
    for word in ["Olivier", "Oliver", "Alivier", "aliver"]:
        trie.insert(word)

    assert trie.fuzzySearch("olivier", 0) == {"olivier"}
    assert trie.fuzzySearch("olivier", 1) == {"oliver", "olivier", "alivier"}
    assert trie.fuzzySearch("olivier", 2) == {"oliver", "olivier", "alivier", "aliver"}

    assert trie.fuzzySearch("olivia", 0) == set()
    assert trie.fuzzySearch("olivia", 1) == set()
    assert trie.fuzzySearch("olivia", 2) == {"oliver", "olivier"}
    assert trie.fuzzySearch("olivia", 3) == {"oliver", "olivier", "alivier", "aliver"}


def test_fuzzy_search_trie(noisy_base_words, trie_search_oracle):
    from simplesearch import Trie

    trie = Trie()
    for word in noisy_base_words(4):
        trie.insert(word)

    for word in noisy_base_words(4):
        for n in range(5):
            assert trie.fuzzySearch(word, n) == trie_search_oracle(trie, word, n)


def test_fuzzy_search_documents(noisy_base_words, index_search_oracle):
    from simplesearch import Index

    words = noisy_base_words(4)
    doc_count = floor(sqrt(len(words)))
    docs = [" ".join(random.sample(sorted(words), doc_count)) for _ in range(doc_count)]

    index = Index(docs)

    for word in noisy_base_words(2):
        for n in range(3):
            assert index.fuzzySearch(word, n) == index_search_oracle(index, word, n)
