"""
Defines the interface and Console implementation of the Receiver for querying the user for input.

Following the Command design pattern, the Receiver participant interface is defined, and the Console implementation is provided.

Exported Classes:
    UserQueryReceiver -- Interface (abstract base) class for Receiver.
    ConsoleUserQueryReceiver -- Concrete UserQueryReceiver that obtains raw (text) responses from user from a Console window.

Exported Exceptions:
    UserQueryReceiverError -- Base exception class from which all custom exceptions specific to UserQueryReceiver should be derived.
    UserQueryReceiverTerminateQueryingThreadError -- Concrete custom exception raised if the UserQueryReceiver wants the querying Client to terminate.
 
Exported Functions:
    UserQueryReceiver_GetCommandReceiver -- Global prebound method that returns the global, single instance of a concrete UserQueryReceiver.
    See for reference:
        (1) Global Object Pattern: https://python-patterns.guide/python/module-globals/
        (2) Prebound Method Pattern: https://python-patterns.guide/python/prebound-methods/
"""

# Standard

# Local

class UserQueryReceiverError(Exception):
    """
    Base exception class for all custom exceptions specific to UserQueryReceiver.
    """
    pass


class UserQueryReceiverTerminateQueryingThreadError(UserQueryReceiverError):
    """
    Custom exception to be raised if the UserQueryReceiver wants the query (command pattern) Client to terminate.
    """

    def __init__(self, *args, **kwargs):
        """
        Extends UserQueryReceiverError.__init__()

        Arguments expected in **kwargs:
            none at this time    
        """
        super().__init__(*args)


class UserQueryReceiver(object):
    """
    Interface (abstract base) class for Receiver of user input query.

    Following the Command design pattern, this is the abstract base or interface class for Receiver classes that know how to perform operations
    required to carry out a concrete UserQueryCommand. We will also be applying the Global Object and Prebound Method patterns.
    
    Each child must by convention and necessity implement these methods:
        GetCommandReceiver() -- Returns self. NOT an abstract method. Typically should NOT be overridden.
        GetRawResponse(...) -- Obtain from the user their actual raw response as a string of text, for example, typed into a console window. 
        IssueErrorMessage(...) -- Inform the user that their raw response does not meet requirements, for example, by printing to a console window.
    """

    def __init__(self):
        """
        Just print a message, temporarily, to see if this works as expected and only ever gets instaniated once.
        """
        print(f"Instaniating: {type(self)}, ID: {id(self)}")
            
    def GetCommandReceiver(self):
        """
        This is a concrete method, intended to be used as the target of a prebound method. It returns self.
            :return: self, UserQueryReceiver object       
        """
        return self
    
    def GetRawResponse(self, prompt_text=''):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        Called to obtain a raw response from the user, which will always be a sting of text.
            :parameter prompt_text: String of text (default='') to use to tell the user what response is requrired, string
            :return: Raw response, string        
        """
        raw_response = ''
        raise NotImplementedError
        return raw_response
    
    def IssueErrorMessage(self, msg=''):
        """
        This is an abstract method that MUST be implemented by children. If called, it will raise NotImplementedError
        Called to inform the user that their raw response does not meet requirements.
            :parameter msg: Error message (default='') to be shown to the user, string
            :return: None       
        """
        raise NotImplementedError
        return None
    
    
class ConsoleUserQueryReceiver(UserQueryReceiver):
    """
    Implements Reciever for user input provided in a Console window.

    Following the Command design pattern, this is a concrete implementation of a UserQueryReceiver, that a concrete UserQueryCommand object
    can use to obtain raw (text) responses from the user through a console window.

    Methods:
        GetRawResponse(...) --- Obtain from the user their actual raw response as a string of text typed into a console window.
        IssueErrorMessage(...) -- Inform the user that their raw response does not meet requirements, by printing message to a console window.
    """

    def __init__(self):
        """
        Extends UserQueryReceiver.__init__().
        """
        UserQueryReceiver.__init__(self)
    
    def GetRawResponse(self, prompt_text=''):
        """
        Obtains response to query from the user through console window.

        Overrides UserQueryReceiver.GetRawResponse(...). Called to obtain a raw response from the user through their interaction with a console window, which will always be a sting of text.
            :parameter prompt_text: String of text (default='') to use to tell the user what response is requrired, string
            :return: Raw response, string        
        """
        # Ask the user to type a text response into the console window, which will be in the form of a string
        raw_response = input(prompt_text)
        return raw_response
    
    def IssueErrorMessage(self, msg=''):
        """
        Inform the user that their raw response does not meet requirements.

        Overrides UserQueryReciever.IssueErrorMessage(...). Prints message to user in console window:
            :parameter msg: Error message (default='') to be shown to the user, string
            :return: None       
        """
        # Let the user know that there was a problem with their response, by printing an error message to the console window
        print(msg)
        return None


# Here is the global (intended to be private), single instance
_instance = ConsoleUserQueryReceiver()

# Here are the global prebound method(s)
UserQueryReceiver_GetCommandReceiver = _instance.GetCommandReceiver
