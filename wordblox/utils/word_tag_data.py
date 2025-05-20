import re
from enum import Enum

"""
    This Enum denotes the action to take in the case
    that both collections have the same key
"""
class SyncMethod(Enum):
    OVERRIDE = 0   
    JOIN = 1


class TupleKeyCollection:

    _JOINER_CHAR = ":"

    key_regex = f"^\w+{_JOINER_CHAR}\w+$"

    _default_details = ""

    @classmethod
    def isValidKey(cls, key: str):
        if type(key) == str and len(key) > 0:
            match = re.search(cls.key_regex, key)
            if match == None:
                return False
            else:
                return True
        else:
            return False
        
    @classmethod
    def isValidValue(cls, val: str):
        return type(val) == str and len(val) >= 0
    
    @classmethod
    def sanitizeValue(cls, val: str):
        """
            Sanitizes Values to stop code injection.

            This is to be done later, once propper regex(s) is found
        """
        return val

    @classmethod
    def combine(cls, tag:str, word:str):
        if type(tag) == str and len(tag) > 0 and type(word) == str and len(word) > 0:
            return f"{tag}{cls._JOINER_CHAR}{word}"
        else:
            return None
        
    @classmethod
    def separate(cls, key: str):
        return key.split(cls._JOINER_CHAR,1)

    def __init__(self):
        self.tag_word_details = {}

    def __iter__(self):
        iterator = []
        for key, val in self.tag_word_details.items():
            tag, word = self.__class__.separate(key)
            iterator.append((tag, word, val))
        return iterator

    def add(self, tag: str, word: str, details: str = ""):
        key = self.__class__.combine(tag, word)
        if key != None:
            self.tag_word_details[key] = details
        else:
            if type(tag) == str and type(word) == str:
                raise TypeError(f"Could not create Type with tag of length: {len(tag)} and word of length: {len(word)}")
            else:
                raise TypeError(f"Could not create Tuple Key with: {type(tag)} and {type(word)}")
        
    def sync(self, other_collection, sync_method: SyncMethod = SyncMethod.OVERRIDE):
        """
            Performs a sync operation with another TupleKeyCollection

            Note: this does not augment the current collection, instead it returns 3 separate collections described as follows:
                old_collection = Items in this collection, but not in the passed collection
                new_collection = Items not in this collection, but are in the passed collection
                both_collection = Items that are in both collections
        """
        if isinstance(other_collection, TupleKeyCollection):
        #if other_collection is TupleKeyCollection:
            new_collection = TupleKeyCollection() # in other_collection, but not in self.tag_word_details dictionary
            old_collection = TupleKeyCollection() # in self.tag_word_details dictionary but not in other_collection
            both_collection = TupleKeyCollection() # in both other_collection and self.tag_word_details
            for tag, word, details in iter(other_collection):
                cur_val = self.get(tag, word)
                if cur_val == None:
                    new_collection.add(tag, word, details)
                elif sync_method == SyncMethod.OVERRIDE:
                    both_collection.add(tag, word, details)
                elif sync_method == SyncMethod.JOIN:
                    both_collection.add(tag, word, cur_val + details)
                else:
                    continue
            for key, val in self.tag_word_details.items():
                if other_collection.getWithKey(key) == None:
                    _ = old_collection.addWithKey(key, val)
                else:
                    continue
            return old_collection, new_collection, both_collection
        elif type(other_collection) == object:
            raise TypeError(f"Can not sync with {other_collection.__class__}")
        else:
            raise TypeError(f"Can not sync with {type(other_collection)}")

    def get(self, tag: str, word: str):
        key = self.__class__.combine(tag, word)
        if key != None:
            val = self.tag_word_details.get(key, None)
            if val != None:
                return val
            else:
                return None
        else:
            return None
        
    def getWithKey(self, key):
        if self.__class__.isValidKey(key):
            return self.tag_word_details.get(key, None)
        else:
            return None
        
    def addWithKey(self, key: str, val: str):
        if self.__class__.isValidKey(key):
            new_val = self.__class__.sanitizeValue(val)
            if not self.__class__.isValidValue(new_val):
                new_val = self.__class__._default_details
            self.tag_word_details[key] = new_val
            return True
        else:
            return False
        

    
