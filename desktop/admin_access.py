import base64
import hashlib
import hmac
import secrets

from desktop.credentials import (
    CredentialStore,
)


ADMIN_PASSWORD_VERIFIER = (
    "admin_password_verifier"
)


class AdminAccess:
    """
    Administrator-password verification.

    The plaintext administrator password is never stored.

    The verifier is stored through CredentialStore:
    - macOS -> Keychain
    - Windows -> Credential Manager
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

    def has_password(
        self,
    ) -> bool:
        return bool(
            self.credential_store.get(
                ADMIN_PASSWORD_VERIFIER
            )
        )

    def set_password(
        self,
        password: str,
    ) -> None:
        if len(password) < 6:
            raise ValueError(
                "administrator password must contain at least 6 characters"
            )

        salt = secrets.token_bytes(
            self.SALT_BYTES
        )

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(
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
            ADMIN_PASSWORD_VERIFIER,
            verifier,
        )

    def verify_password(
        self,
        password: str,
    ) -> bool:
        verifier = (
            self.credential_store.get(
                ADMIN_PASSWORD_VERIFIER
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
            password.encode(
                "utf-8"
            ),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            actual,
            expected,
        )
