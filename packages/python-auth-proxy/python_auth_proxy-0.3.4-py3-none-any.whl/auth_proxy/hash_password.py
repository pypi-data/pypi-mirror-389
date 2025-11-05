import argparse
import getpass
import sys

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with a random salt.

    Args:
        password: The password to hash

    Returns:
        The hashed password as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def main() -> None:
    """Main entry point for the password hashing utility."""
    parser = argparse.ArgumentParser(
        description="Hash a password for use with auth-proxy basic authentication"
    )
    parser.add_argument(
        "-p",
        "--password",
        help="Password to hash (if not provided, will prompt securely)",
    )
    parser.add_argument("--verify", help="Verify a password against a hash")
    args = parser.parse_args()

    if args.verify:
        # Verify mode
        if args.password:
            password = args.password
        else:
            password = getpass.getpass("Enter password to verify: ")

        try:
            if bcrypt.checkpw(password.encode("utf-8"), args.verify.encode("utf-8")):
                print("Password matches hash!")
                sys.exit(0)
            else:
                print("Password does not match hash!")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying password: {e}")
            sys.exit(1)
    else:
        # Hash mode
        if args.password:
            password = args.password
        else:
            password = getpass.getpass("Enter password to hash: ")
            confirm = getpass.getpass("Confirm password: ")

            if password != confirm:
                print("Passwords do not match!")
                sys.exit(1)

        hashed = hash_password(password)
        print(f"Hashed password: {hashed}")
        print("\nYou can use this in your config file like:")
        print(f'    username: "{hashed}"')


if __name__ == "__main__":
    main()
