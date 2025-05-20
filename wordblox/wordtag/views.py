from rest_framework import viewsets
from .models import Word, Tag, Domain
from .serializers import TagSerializer, WordSerializer
from utils.fetch_word_data import ExternalServerFetchException, FetchController
from django.http import HttpResponse, JsonResponse
from utils.json_input_handler import LoginDomainLockedJsonHandler
from utils.word_tag_data import TupleKeyCollection, SyncMethod
import json
from enum import Enum

class SyncError(Exception):

    def __init__(self, message):
        super().__init__(message)

class CollectionPriority:
    CACHED = 0
    EXTERNAL = 1

class SyncControl:
    MERGE = 0   # This refers to merging the rows that do not exist in both Cached and External
    DELETE = 1  # This refers to the completely overwritting the database based on CollectionPriority

# Create your views here.
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer

def getWordTagObject(word_tag):
    word = word_tag.get('word', None)
    tag = word_tag.get('tag', None)
    details = word_tag.get('details', "")
    return tag, word, details

class DomainError(Exception):

    def __init__(self, message):
        super().__init__(message)

class NullDomainError(DomainError):

    def __init__(self, message):
        super().__init__(message)

class UnknownDomainError(DomainError):

    def __init__(self, message, domain):
        super().__init__(f"Can Not Find {domain}: {message}")


class SyncHandler:
    """
        Handler for Sync'ing Cached database with data from the external source.

        Currently uses 3 settings to control how the sync is applied.
    """

    # ----- Default values for the Sync Settings -----

    _default_syncMethod = SyncMethod.OVERRIDE   # What to do in the case of key collisions
    _default_syncPriority = CollectionPriority.EXTERNAL # Which collection takes presendence when necessary
    _default_syncControls = SyncControl.MERGE   # The action to take when faced with data that does not exist in both Cached and External data stores

    # ------ Validation and Sanitization for the Database -----

    _default_details = ""

    @classmethod
    def isValidDomain(cls, domain):
        return type(domain) and len(domain) > 0

    @classmethod
    def isValidTag(cls, tag):
        return type(tag) == str and len(tag) > 0
    
    @classmethod
    def isValidWord(cls, word):
        return type(word) == str and len(word) > 0
    
    @classmethod
    def isValidDetails(cls, details=""):
        return type(details) == str
    
    @classmethod
    def sanitizeDetails(cls, details=""):
        if cls.isValidDetails(details):
            return details
        else:
            return cls._default_details
        
    # ----- Validation and Sanitization for the various settings for Syncing -----

    @classmethod
    def isValidSyncMethod(cls, syncMethod: SyncMethod):
        return syncMethod in SyncMethod
    
    @classmethod
    def sanitizeSyncMethod(cls, syncMethod: SyncMethod):
        if cls.isValidSyncMethod(syncMethod):
            return syncMethod
        else:
            return cls._default_syncMethod
        
    @classmethod
    def isValidSyncControl(cls, syncControl: SyncControl):
        return syncControl in SyncControl
    
    @classmethod
    def sanitizeSyncControl(cls, syncControl: SyncControl):
        if cls.isValidSyncControl(syncControl):
            return syncControl
        else:
            return cls._default_syncControl

    @classmethod
    def isValidSyncPriority(cls, syncPriority: CollectionPriority):
        return syncPriority in CollectionPriority
    
    @classmethod
    def sanitizeSyncPriority(cls, syncPriority: CollectionPriority):
        if cls.isValidSyncPriority(syncPriority):
            return syncPriority
        else:
            return cls._default_syncPriority
        
    # ----- Methods for handling the sync process -----

    @classmethod
    def removeFromCache(cls, collection, domain):
        """
            This function removes things from the cache database for a given domain

            @param  {TupleKeyCollection}    collection  The collection storing the data to remove
            @param  {string}    domain  This controls the scope of database operations
        """
        if not cls.isValidDomain(domain):
            raise DomainError(f"Can not process the given domain: {domain}")
        #if isinstance(collection, TupleKeyCollection):
        if collection is TupleKeyCollection:
            for tup in iter(collection):
                if len(tup) == 3:
                    tag, word, _ = tup
                elif len(tup) == 2:
                    tag, word = tup
                else:
                    continue
                if not cls.isValidTag(tag) or not cls.isValidWord(word):
                    cls.logger.error(f"Could not remove the tag, word tuple: ({tag}, {word})")
                    continue
                else:
                    try:
                        wordtag = Word.objects.get(text=word, tag__text=tag, tag__domian__url=domain)
                    except Word.DoesNotExist:
                        wordtag = None
                    finally:
                        if wordtag:
                            wordtag.delete()
        else:
            raise TypeError(f"Expected a TupleKeyCollection, instead got: {collection.__class__}")

    @classmethod
    def addToCache(cls, collection, domain):
        """
            This will add a collection to the Cache database under a given domain.
            This function does handle updates as well as add.

            For a given (tag, word) pair in the collection, this function will do one of the following:
                (1) If (tag, word) does not exist, add the word, and tag if necessary, and set its details
                (2) If (tag, word) does exist, if the details in the collection are different, update, otherwise do nothing. 

            @param  {TupleKeyCollection}    collection  The collection to add. 
            @param  {string}    domain  This controls the scope of database operations
        """
        if not cls.isValidDomain(domain):
            raise DomainError(f"Can not process the given domain: {domain}")
        #if isinstance(collection, TupleKeyCollection):
        if collection is TupleKeyCollection:
            for tup in iter(collection):
                if len(tup) == 3:
                    tag, word, details = tup
                elif len(tup) == 2:
                    tag, word = tup
                    details = ""
                else:
                    continue
                if not cls.isValidTag(tag) or not cls.isValidWord(word):
                    cls.logger.error(f"Could not add/update the tag, word tuple: ({tag}, {word})")
                    continue
                else:
                    sanitized_details = cls.sanitizeDetails(details)
                    try:
                        wordtag = Word.objects.get(text=word, tag__text=tag, tag__domain__url=domain)
                        if word.details != sanitized_details:
                            wordtag.details = sanitized_details
                            wordtag.save()
                    except Word.DoesNotExist as e:
                        try:
                            tagObj = Tag.objects.get(text=tag, domain__url=domain)
                        except Tag.DoesNotExist:
                            try:
                                domainObj = Domain.objects.get(url=domain)
                            except Domain.DoesNotExist:
                                raise SyncError(f"Can not find a Domain object with url: {domain}")
                            tagObj = Tag(text=tag, domain=domainObj)
                            tagObj.save()
                        finally:
                            word = Word(text=word, tag=tagObj, details=sanitized_details)
                            word.save()
        else:
            raise TypeError(f"Expected a TupleKeyCollection, instead got: {collection.__class__}")

    @classmethod
    def syncExternalAndCached(cls, externalData, cachedData, domain, syncMethod: SyncMethod = SyncMethod.OVERRIDE, syncPriority: CollectionPriority=CollectionPriority.EXTERNAL, syncControl: SyncControl = SyncControl.MERGE):
        """
            Syncs the Cache database with the External data for a given domain. Additionally, this function is passed 3 control variables in the form of enums
            that control order and methods used to perform any sync.

            The sync is performed by using the 2 given collections to build 3 collections, each one representing one of the following states:
                (1) Only in Collection A
                (2) Only in Collection B
                (3) In both Collection A and B

            It is done in this way so that it becomes possible to easily change the way Sync will work in the future, such as displaying conflicts (3) to
            the user and asking for input. Currently, it just concats the values stored in each of the collections, but there is a use case of giving a user
            control of resolving conflicts (such as seen in GIT and SVN)

            Note:   
                This function should be refactored to use batch transactions in the next stage, in order to reduce the database operations, which is why
                the system builds two different collections (externalData & cachedData)

            @param  {TupleKeyCollection}    externalData    
        """
        if not cls.isValidDomain(domain):
            raise DomainError(f"Can not process the given domain: {domain}")
        if isinstance(externalData, TupleKeyCollection) and isinstance(cachedData, TupleKeyCollection):
        #if externalData is TupleKeyCollection and cachedData is TupleKeyCollection:
            syncMethod = cls.sanitizeSyncMethod(syncMethod)
            syncPriority = cls.sanitizeSyncPriority(syncPriority)
            syncControl = cls.sanitizeSyncControl(syncControl)
            try:
                if syncPriority == CollectionPriority.EXTERNAL:
                    old_collection, new_collection, both_collection = cachedData.sync(externalData, syncMethod)  
                elif syncPriority == CollectionPriority.CACHED:
                    old_collection, new_collection, both_collection = externalData.sync(cachedData, syncMethod)
                else:
                    # This is only raised if there is a sync priority value added the enum, but not implemented
                    raise NotImplementedError(f"Sync Priority was a value that is not implemented as yet. {syncPriority.name}: {syncPriority.value}")
                if syncControl == SyncControl.DELETE and syncPriority == CollectionPriority.EXTERNAL:
                    # Delete old_collection as its the cached data
                    cls.removeFromCache(old_collection, domain)
                # Add the new_collection to the cache
                cls.addToCache(new_collection, domain)
                # update the both_collection if necessary
                cls.addToCache(both_collection, domain)
                # This needs to change to perform it on the models I think
            except Exception as e:
                cls.logger.error(e)
                raise e
        else:
            raise TypeError(f"Expected TupleKeyCollections for parameters externalData and cachedData, instead got: {externalData.__class__}, {cachedData.__class__}") 

class SpellinBloxPullHandler(LoginDomainLockedJsonHandler):
    """
        Handler for handling pull communication with the External SpellinBlox server.

        This class handles the login for the SpellinBlox server, as well as creating the TupleKeyCollections used by
        the Sync handler and starting the process.

        The goal of this class is to provide a single endpoint for pulling data from SpellinBlox.
        
    """

    @classmethod
    def getAllCachedData(cls, domain):
        """
            Creates a TupleKeyCollection, scoped by a domain, from the internal cache database

            @param  {string}    domain  The domain that controlls the scope of the data fetched.

            @return {TupleKeyCollection}    The collection representing the data retreived.
        """
        if type(domain) != str:
             raise UnknownDomainError(f"Can not use domain: {type(domain)}")
        elif len(domain) <= 0:
            raise UnknownDomainError(f"Can not find domain with length: {len(domain)}")
        else:
            cached_wordtags = TupleKeyCollection()
            words = Word.objects.filter(tag__domain__url=domain).values_list("tag__text", "text", "details")
            if len(words) > 0:
                for tup in words:
                    if len(tup) == 3:
                        tag, word, details = tup
                    elif len(tup) == 2:
                        tag, word = tup
                        details = ""
                    else:
                        continue
                    cached_wordtags.add(tag, word, details)
            return cached_wordtags
        
    @classmethod
    def getAllExternalData(cls, controller, domain):
        """
            Creates a TupleKeyCollection, scoped by a domain, from the External SpellinBlox server

            @param  {FetchController}   controller  The controller for fetching over the Internet
            @param  {string}    domain  The domain that controlls the scope of the data fetched.

            @return {TupleKeyCollection}    The collection representing the data retreived.
        """
        #if isinstance(controller, FetchController):
        if controller is FetchController:
            # Change this to be more specific errors
            raise TypeError(f"Controller expected to be a FetchController, instead got: {type(controller)}")
        if type(domain) != str:
             raise UnknownDomainError(f"Can not use domain: {type(domain)}")
        elif len(domain) <= 0:
            raise UnknownDomainError(f"Can not find domain with length: {len(domain)}")
        else:
            domain_data = {}
            try:
                domain_data = controller.getData(domain)
            except ExternalServerFetchException as e:
                cls.logger.error(f"Fetch Data Error: {e}")
            except Exception as e:
                cls.logger.error(f"Unknown Error: {e}")
            finally:
                word_tag_collection = TupleKeyCollection()
                if type(domain_data) == dict:
                    wordtag_list = domain_data.get("wordtags", [])
                    for i in range(len(wordtag_list)):
                        tag, word, details = getWordTagObject(wordtag_list[i])
                        try:
                            word_tag_collection.add(tag, word, details)
                        except TypeError as e:
                            cls.logger.error(f"Collection Add Error: {e}")
                        except Exception as e:
                            cls.logger.error(f"Unknown Error: {e}")
                return word_tag_collection
        

    @classmethod
    def post_input(cls, request):
        """
            The actions associated with the SpellinBlox Pull Handler POST request input.

            Initiates a sync in the local cache with data from the SpellinBlox server based
            on parameters passed via POST request.
        """
        data = json.loads(request.body)
        domain = data.get("domain", "")
        username = data.get("username", "")
        password = data.get("password", "")
        controller = FetchController()
        auth_check = False
        err_msg = "Unknown Error"
        sync_err_msg = ""
        try:
            controller.auth(username, password)
            auth_check = True
        except ExternalServerFetchException as e:
            auth_check = False # Just in case and for clarity
            cls.logger.error(f"Authentication Error: {e}")
            err_msg = f"Authentication Error: {e}"
        except Exception as e:
            auth_check = False # Just in case and for clarity
            cls.logger.error(f"Authentication Failed, Error Unknown {e}")
            err_msg = f"Authentication Failed, Error Unknown: {e}"
        finally:
            if auth_check:
                external_wordtags = None
                cached_wordtags = None
                try:
                    external_wordtags = cls.getAllExternalData(controller, domain)
                except TypeError as e:
                    cls.logger.error(f"FetchController failed: {e}")
                    return HttpResponse(f"FetchController failed: {e}", status=500)
                except DomainError as e:
                    cls.logger.error(f"Domain Error with External Data: {e}")
                    return HttpResponse(f"FetchController failed: {e}", status=400)
                finally:
                    controller.quit()
                try:
                    cached_wordtags = cls.getAllCachedData(domain)
                except DomainError as e:
                    cls.logger.error(f"Domain Error with Cached Data: {e}")
                    return HttpResponse(f"FetchController failed: {e}", status=400)
                syncCompleted = False
                try:
                    SyncHandler.syncExternalAndCached(external_wordtags, cached_wordtags, domain)
                    syncCompleted = True
                except Exception as e:
                    syncCompleted = False
                    sync_err_msg = f"{e}"
                finally:
                    return JsonResponse({'syncCompleted': syncCompleted, 'syncErr': sync_err_msg})
            else:
                # Do something is authentication failed
                controller.quit()
                return HttpResponse(err_msg, status=403)
            
class SpellinBloxPushHandler(LoginDomainLockedJsonHandler):
    """
        This is the class for handling the push communication for the external SpellinBlox server
    """

    # TO DO
    pass