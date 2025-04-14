from django.core.exceptions import ValidationError


class ContainsUppercaseValidator:
    """
    Validates whether the password contains at least min_uppercase uppercase characters.

    Adapted from https://github.com/ezrajrice/django_advanced_password_validation/tree/main
    No translations here.
    """

    def __init__(self, min_uppercase=1):
        """Initializes the validator.

        Args:
            min_uppercase (int, optional): Minimum number of uppercase characters to
                validate password against. Defaults to 1.
        """
        self.min_uppercase = min_uppercase

    def validate(self, password, user=None):
        """
        Validates whether the password contains at least min_uppercase uppercase characters.

        Args:
            password (str): The password to validate.
            user (User): The user to validate the password for. (unused)

        Raises:
            ValidationError: Password must contain at least {self.min_uppercase} uppercase
                character(s).
        """
        if sum(c.isupper() for c in password) < self.min_uppercase:
            raise ValidationError(
                f"Salasanan täytyy sisältää vähintään {self.min_uppercase} iso{'a' if self.min_uppercase > 1 else ''} kirjain{'ta' if self.min_uppercase > 1 else ''}.",
                code="password_too_weak",
            )

    def get_help_text(self):
        """
        Get the help text for the validator.
        """
        return f"Salasanan täytyy sisältää vähintään {self.min_uppercase} iso{'a' if self.min_uppercase > 1 else ''} kirjain{'ta' if self.min_uppercase > 1 else ''}."


class ContainsSpecialCharactersValidator:
    """
    Validates whether the password contains at least min_characters special characters.
    """

    def __init__(self, min_characters=1):
        """Initializes the validator.

        Args:
            min_characters (int, optional): Minimum number of special characters to
                validate password against. Defaults to 1.
        """
        self.min_characters = min_characters
        self.characters = " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

    def validate(self, password, user=None):
        """
        Validates whether the password contains at least min_characters special characters.

        Args:
            password (str): The password to validate.
            user (User): The user to validate the password for. (unused)

        Raises:
            ValidationError: Password must contain at least {self.min_characters} special
                character(s).
        """
        if sum(c in set(self.characters) for c in password) < self.min_characters:
            raise ValidationError(
                f"Salasanan täytyy sisältää vähintään {self.min_characters} "
                f"erikoismerkki{'ä' if self.min_characters > 1 else ''} joukosta: {self.characters}",
                code="password_too_weak",
            )

    def get_help_text(self):
        """
        Get the help text for the validator.
        """
        return (
            f"Salasanan täytyy sisältää vähintään {self.min_characters} "
            f"erikoismerkki{'ä' if self.min_characters > 1 else ''} joukosta: {self.characters}"
        )
