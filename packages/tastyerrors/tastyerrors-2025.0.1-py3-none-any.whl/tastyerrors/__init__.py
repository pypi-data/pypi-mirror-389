'''

Copyright 2025 Arjun Singh

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''

# --- Base Package Exception ---
class TastyErrors(Exception):
    """
    The base class for all application-level exceptions within the 'tastyerrors' package.
    Catching this exception will handle any custom error defined in this library.
    """
    pass


# --- Authorization Errors ---
class AuthError(TastyErrors):
    """Base exception for all authentication and authorization failures."""
    pass
class UsernameNotFound(AuthError):
    """Raised when the provided username does not exist in the system."""
    pass
class IncorrectPassword(AuthError):
    """
    Raised when a user provides an incorrect password for an existing account.
    Use BadPassword for general validation failures.
    """
    pass
class BadAdminRequest(AuthError):
    """
    Raised when an operation requiring administrator privileges fails due to insufficient
    permissions or an incorrect admin credential check.
    """
    pass
class BadDatabaseConnection(AuthError):
    """Raised when an attempt to connect or maintain connection to a database fails."""
    pass
class IncorrectRecoveryCode(AuthError):
    """Raised when an invalid recovery code is provided during a multi-factor authentication procedure."""
    pass
class Failed2FAAuthentication(AuthError):
    """Raised when a user fails to complete a required two-factor authentication process."""
    pass
class RetryLimitExceededError(AuthError):
    """Raised when a user or process exceeds the maximum allowed number of attempts (e.g., login retries)."""
    pass
# End Auth Errors

# --- Input and Validation Errors ---
class BadPassword(TastyErrors):
    """Base exception for password validation issues (formatting, strength, etc.)."""
    pass
class BadUsername(TastyErrors):
    """Base exception for username validation issues."""
    pass
class InputError(TastyErrors):
    """Base exception for problems with user-supplied input data."""
    pass

class PasswordTooShort(BadPassword):
    """Raised when the provided password does not meet the minimum required length."""
    pass
class NotUniqueUsername(BadUsername):
    """Raised when a new username is supplied that already exists in the system."""
    pass
class NotUniquePassword(BadPassword):
    """Raised when a password is rejected due to a policy disallowing recently used passwords."""
    pass
class BadType(TypeError):
    """Raised when an argument is of an inappropriate type (e.g., a string is passed where an integer is required)."""
    pass
class InappropriateUsername(BadUsername):
    """Raised if the username contains forbidden characters or patterns."""
    pass
class InappropriatePassword(BadPassword):
    """Raised if the password contains forbidden characters or patterns."""
    pass
class BadPrompt(InputError):
    """Raised when a request or prompt to a system is poorly formed or syntactically invalid."""
    pass

# --- Color Picking Exceptions (New) ---
class ColorError(InputError):
    """Base exception for errors related to invalid or unacceptable color values."""
    pass
class InvalidColorFormatError(ColorError):
    """Raised when a color value is not in a recognized format (e.g., not a valid hex code or RGB tuple)."""
    pass
class ColorNotInPaletteError(ColorError):
    """Raised when a color is valid but is explicitly disallowed by the current application's limited color palette."""
    pass
# End Color Picking Exceptions

# End Input Errors

# --- Data, State, and Logic Errors ---
class DataNotFoundError(TastyErrors):
    """Raised when a requested data record or resource cannot be located in storage or cache."""
    pass
class InvalidStateError(TastyErrors):
    """Raised when an action is attempted while the system or object is in an inappropriate state (e.g., calling 'stop' before 'start')."""
    pass
class ProcessingError(TastyErrors):
    """Base exception for errors that occur during the execution of a task or business logic."""
    pass
class LogicError(TastyErrors):
    """Raised when an execution path is reached that should be logically impossible, indicating a flaw in the program's design."""
    pass
# End Data/Logic Errors

# --- Resource and File Errors ---
class CorruptFile(TastyErrors):
    """Raised when a file's content is unreadable or fails a content integrity check."""
    pass
class ConfigException(FileNotFoundError):
    """Raised when a configuration file is expected but either cannot be found or its content is invalid."""
    pass
class InsufficientFundsError(TastyErrors):
    """Raised in financial or resource management contexts when a transaction fails due to a negative balance."""
    pass
class InventoryError(TastyErrors):
    """Raised when an operation fails because required inventory or stock is insufficient or depleted."""
    pass
# End Resource/File Errors

# --- System and Concurrency Errors ---
class MemoryExhaustedError(SystemError):
    """Raised when an operation fails due to insufficient available memory (RAM)."""
    pass
class ResourcesExhaustedError(SystemError):
    """Raised when an operation fails due to the exhaustion of a non-memory resource (e.g., file descriptors, thread pool capacity)."""
    pass
class SpaceUnavailableError(SystemError):
    """Raised when an operation requiring disk space fails because the file system is full."""
    pass
class ConcurrencyException(SystemError):
    """Raised when a multi-threaded operation fails due to a conflict or deadlock."""
    pass
class DependencyError(SystemError):
    """Raised when a required internal or external dependency is missing or failed to initialize."""
    pass
# End System Errors

# --- New Processing Subtypes (for 40+ count) ---
class RateLimitExceededError(ProcessingError):
    """Raised when an application or user exceeds the allowed number of requests to a service or API within a time window."""
    pass
class DataIntegrityError(ProcessingError):
    """Raised when data retrieved or processed fails a critical validation or integrity check (e.g., checksum failure, foreign key violation)."""
    pass
# End New Subtypes

# --- Network and External Service Errors ---
class UnavailableResourceError(ConnectionError):
    """Raised when an external resource or server is temporarily unreachable or offline."""
    pass
class ServiceNotAvailable(ConnectionRefusedError):
    """Raised when a connection attempt is actively rejected by the target server or service."""
    pass
class TimeOutException(TimeoutError):
    """Raised when an operation or network request exceeds its maximum allowed duration."""
    pass
class NetworkError(ProcessingError):
    """A general exception for non-specific problems occurring during network communication."""
    pass
class APIException(ProcessingError):
    """Raised when an external API returns a non-successful status or an unexpected error payload."""
    pass
class InternalServerError(RuntimeError):
    """Raised to wrap or represent an unexpected, internal error that is not directly attributable to user input."""
    pass
# End Network Errors
