"""
Módulo: tests/test_security.py
Descripción: Tests unitarios de las funciones puras de app/utils/security.py.
¿Para qué? Probar el hashing de contraseñas y los tokens JWT de forma aislada: sin HTTP,
           sin endpoints y sin datos en la BD. Cada test sigue el patrón AAA.
¿Impacto? Son los tests más rápidos de la suite y señalan el error exacto: si falla
          `decode_token`, se sabe que el problema está en el JWT y no en un endpoint.
"""

from datetime import timedelta

from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests del hashing de contraseñas con bcrypt."""

    def test_hash_password_does_not_store_the_plain_password(self) -> None:
        # Arrange
        password = "Segura123"

        # Act
        hashed = hash_password(password)

        # Assert
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_when_password_is_wrong(self) -> None:
        hashed = hash_password("Segura123")

        assert verify_password("Incorrecta123", hashed) is False


class TestAccessToken:
    """Tests de creación y verificación de access tokens JWT."""

    def test_decode_token_returns_subject_and_type_when_token_is_valid(self) -> None:
        # Arrange
        token = create_access_token(data={"sub": "ana@nn-company.com"})

        # Act
        payload = decode_token(token)

        # Assert
        assert payload is not None
        assert payload["sub"] == "ana@nn-company.com"
        assert payload["type"] == "access"

    def test_decode_token_returns_none_when_token_is_expired(self) -> None:
        # ¿Qué? Un expires_delta negativo crea un token que ya venció: se controla el tiempo
        #       por parámetro, sin esperar ni congelar el reloj.
        token = create_access_token(
            data={"sub": "ana@nn-company.com"}, expires_delta=timedelta(minutes=-1)
        )

        assert decode_token(token) is None

    def test_decode_token_returns_none_when_payload_was_modified_after_signing(self) -> None:
        # Arrange: se altera el contenido (payload) sin volver a firmarlo.
        # ¿Por qué no el último carácter de la firma? En base64url ese carácter tiene bits de
        # relleno: cambiar "A" por "B" puede dejar la firma idéntica y el test fallaría al azar.
        token = create_access_token(data={"sub": "ana@nn-company.com"})
        header, payload, signature = token.split(".")
        tampered_payload = ("e" if payload.startswith("f") else "f") + payload[1:]
        tampered = f"{header}.{tampered_payload}.{signature}"

        # Act / Assert
        assert decode_token(tampered) is None
