import base64
import hashlib
import hmac
import secrets

from desktop.credentials import CredentialStore


ADMIN_PIN_VERIFIER = "admin_pin_verifier"


class AdminPin:
    """
    Six-digit administrator PIN protection.

    Plaintext PIN values are never persisted.

    Only a PBKDF2 verifier with a random salt is stored
    through CredentialStore.
    """

    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 310_000
    SALT_BYTES = 16

    def __init__(
        self,
        credential_store: CredentialStore,
    ) -> None:
        self.credential_store = (
            credential_store
        )

    @staticmethod
    def is_valid_format(
        value: str,
    ) -> bool:
        return (
            len(value) == 6
            and value.isascii()
            and value.isdigit()
        )

    def has_pin(
        self,
    ) -> bool:
        return bool(
            self.credential_store.get(
                ADMIN_PIN_VERIFIER
            )
        )

    def set_pin(
        self,
        value: str,
    ) -> None:
        if not self.is_valid_format(
            value
        ):
            raise ValueError(
                "administrator PIN must be exactly 6 digits"
            )

        salt = secrets.token_bytes(
            self.SALT_BYTES
        )

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode(
                "utf-8"
            ),
            salt,
            self.ITERATIONS,
        )

        salt_text = (
            base64.urlsafe_b64encode(
                salt
            ).decode(
                "ascii"
            )
        )

        digest_text = (
            base64.urlsafe_b64encode(
                digest
            ).decode(
                "ascii"
            )
        )

        verifier = (
            f"{self.ALGORITHM}"
            f"${self.ITERATIONS}"
            f"${salt_text}"
            f"${digest_text}"
        )

        self.credential_store.set(
            ADMIN_PIN_VERIFIER,
            verifier,
        )

    def verify_pin(
        self,
        value: str,
    ) -> bool:
        if not self.is_valid_format(
            value
        ):
            return False

        verifier = (
            self.credential_store.get(
                ADMIN_PIN_VERIFIER
            )
        )

        if not verifier:
            return False

        try:
            (
                algorithm,
                iterations_text,
                salt_text,
                expected_text,
            ) = verifier.split(
                "$",
                3,
            )

            if (
                algorithm
                != self.ALGORITHM
            ):
                return False

            iterations = int(
                iterations_text
            )

            salt = (
                base64.urlsafe_b64decode(
                    salt_text.encode(
                        "ascii"
                    )
                )
            )

            expected = (
                base64.urlsafe_b64decode(
                    expected_text.encode(
                        "ascii"
                    )
                )
            )

        except (
            ValueError,
            TypeError,
        ):
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode(
                "utf-8"
            ),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            actual,
            expected,
        )
