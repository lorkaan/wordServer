
class SpellinBloxPushDataCrafter:

    # ----- List of keys that the SpellinBlox server is expecting -----

    domain_key = "domain"

    word_tag_list_key = "words"

    word_key = "word"

    tag_key = "tag"

    details_key = "details"

    # ----- Function that pushes the cache to the server -----

    @classmethod
    def createTagWordDetailsDict(cls, tag, word, details=""):
        ret = {}
        ret[cls.tag_key] = tag
        ret[cls.word_key] = word
        ret[cls.details_key] = details
        return ret

    @classmethod
    def pushCacheToServer(cls, collection, domain):
        """
            Not implemented as yet. To be done in a future implementation
        """
        ret = {}
        ret[cls.domain_key] = domain
        tag_word_details_list = []
        for tup in collection.toList():
            if len(tup) >= 3:
                cur = cls.createTagWordDetailsDict(tup[0], tup[1], tup[3])
            elif len(tup) == 2:
                cur = cls.createTagWordDetailsDict(tup[0], tup[1])
            else:
                cur = None
            if cur != None:
                tag_word_details_list.append(cur)
        ret[cls.word_tag_list_key] = tag_word_details_list
        return ret
