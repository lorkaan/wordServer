
class SpellinBloxPushDataCrafter:

    # ----- List of keys that the SpellinBlox server is expecting -----

    word_tag_list_key = "words"

    word_key = "word"

    tag_key = "tag"

    details_key = "details"

    # ----- Function that pushes the cache to the server -----

    @classmethod
    def pushCacheToServer(cls, collection, domain):
        """
            Not implemented as yet. To be done in a future implementation
        """
        raise NotImplementedError("Pushing the Cache to the server is not available yet.")