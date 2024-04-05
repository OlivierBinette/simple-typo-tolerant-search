import string
from collections import defaultdict


class Node:
    def __init__(self, word="", parent=None):
        self.word = word
        self.parent = parent
        self.children = defaultdict()
        self.dists = None
        self.is_word = False


class Trie:
    def __init__(self):
        self.root = Node()

    def preprocess(self, doc):
        return (
            doc.lower()
            .translate(str.maketrans("", "", string.punctuation))
            .encode("ascii", "replace")
            .decode()
        )

    def insert(self, word):
        word = self.preprocess(word)
        node = self.root
        for i, char in enumerate(word):
            node = node.children.setdefault(char, Node(word[: i + 1], node))
        node.is_word = True

    def fuzzySearch(self, query, n):
        query = self.preprocess(query)
        matching_set, visited, stack = set(), set(), [self.root]
        while stack:
            node = stack.pop()
            if node not in visited:
                node.dists = self.get_levenshtein_dists(node, query, n)
                if node.is_word and node.dists[-1] <= n:
                    matching_set.add(node.word)
                if min(node.dists) <= n:
                    stack.extend(node.children.values())
        return matching_set

    def get_levenshtein_dists(self, node, query, n):
        if node.parent is None:
            return range(len(query) + 1)
        dists = [n + 1] * (len(query) + 1)
        dists[0] = len(node.word)
        prev_dists = node.parent.dists
        for i in range(max(0, dists[0] - n - 1), min(len(query), dists[0] + n + 1)):
            dists[i + 1] = (
                prev_dists[i]
                if query[i] == node.word[-1]
                else 1 + min(prev_dists[i], prev_dists[i + 1], dists[i])
            )

        return dists


class Index:
    def __init__(self, documents):
        self.trie = Trie()
        self.inverted_index = defaultdict(lambda: set())
        for doc in documents:
            for word in self.trie.preprocess(doc).split():
                self.trie.insert(word)
                self.inverted_index[word].add(doc)

    def fuzzySearch(self, query, n):
        return {
            doc
            for word in self.trie.fuzzySearch(query, n)
            for doc in self.inverted_index[word]
        }
