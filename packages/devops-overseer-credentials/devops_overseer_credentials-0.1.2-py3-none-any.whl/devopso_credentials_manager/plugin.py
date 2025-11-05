import os
import logging

from pathlib import Path
from devopso.core.configuration import Configuration, Error as ConfigurationError
import devopso.cli
from devopso.adapters.atlassian_adapter import Atlassian

class CredentialsManager:
    def __init__(self, args):
        self._logger = self.get_plugin_logger( "credential-manager" )
        self._args = args
        
    def get_plugin_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        root_logger = logging.getLogger(devopso.cli._APP_LOGGER_NAME)
        for handler in root_logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        return logger
    
    def validate(self):
      self._logger.debug(f"Performing '{self._args.command}' on credentials:")
      self._logger.debug(f"  User: {self._args.user}")
      self._logger.debug(f"  Password: {'*' * len(self._args.password)}")
      self._logger.debug(f"  Application: {self._args.application}")
      self._logger.debug(f"  Type: {self._args.type}")
      self._logger.debug(f"  File path: {self._args.file_path}")
      
      commands_requiring_credentials = {"add", "a", "update", "u"}

      if self._args.command in commands_requiring_credentials:
          if not self._args.user or not self._args.password:
              self._logger.error("❌ Error: 'user' and 'password' are required for this command.")
              exit(1)
        
    
    def add_credentials(self, app_credentials, application: str, user: str, password: str, auth_type: str):
        if not app_credentials:
            app_credentials = { "apps": {}}
        self._logger.info(f"🟢 Adding credentials for user '{application}'")
        if application in app_credentials["apps"]:
            raise ConfigurationError(self._args.file_path, "can't add already existing application, consider updating or removing it first")
        app_credentials['apps'][application] = {
            "login": user,
            "api-token": password,
            "auth-type": auth_type
        }
        Configuration.write_yaml(Path(self._args.file_path).expanduser().resolve(strict=False), app_credentials)
    
    def remove_credentials( self, app_credentials, application: str):
        if not app_credentials:
            self._logger.error("❌ Error: nothing to remove")
            exit(1)
        if application not in app_credentials["apps"]:
            self._logger.error("❌ Error: nothing to remove")
            exit(1)
        
        self._logger.info(f"🔴 Removing credentials for application '{application}'")
        app_credentials["apps"].pop(application)
        Configuration.write_yaml(Path(self._args.file_path).expanduser().resolve(strict=False), app_credentials)
        
    
    def update_credentials(self, app_credentials, application: str, user: str, password: str, auth_type: str):
        if not app_credentials:
            self._logger.error("❌ Error: nothing to update")
            exit(1)
        if application not in app_credentials["apps"]:
            self._logger.error("❌ Error: nothing to update")
            exit(1)
        self._logger.info(f"🟡 Updating credentials for application '{application}'")
        app_credentials['apps'][application] = {
            "login": user,
            "api-token": password,
            "auth-type": auth_type
        }
        Configuration.write_yaml(Path(self._args.file_path).expanduser().resolve(strict=False), app_credentials)

    def run(self):
      self.validate()
      
      app_credentials = Configuration.read_configuration(Path(self._args.file_path).expanduser().resolve(strict=False))
      
      match self._args.command:
          case "a" | "add":
              self.add_credentials(app_credentials, self._args.application, self._args.user, self._args.password, self._args.type)
          case "rm" | "remove":
              self.remove_credentials( app_credentials, self._args.application )
          case "u" | "update":
              self.update_credentials(app_credentials, self._args.application, self._args.user, self._args.password, self._args.type)
          case _:
              self._logger.info(f"⚠️ Unknown command: {self._args.command}")

    @staticmethod
    def execute(args):
        CredentialsManager(args).run()

def register(subparsers):
    parser = subparsers.add_parser(
        "credentials",
        help="Adds, removes, or updates local credentials"
    )

    parser.add_argument(
        "command",
        type=str,
        choices=["add", "remove", "update", "a", "rm", "u"],
        help="Subcommand to perform on the credentials"
    )

    parser.add_argument(
        "-u", "--user",
        required=False,
        type=str,
        default="",
        help="Username or identifier"
    )

    parser.add_argument(
        "-p", "--password",
        required=False,
        type=str,
        default="",
        help="Password or token"
    )

    parser.add_argument(
        "-a", "--application",
        required=True,
        type=str,
        help="Application bound to credentials"
    )

    parser.add_argument(
        "-t", "--type",
        required=False,
        type=str,
        default="Basic",
        help="Authentication type, Basic | Bearer (optional, defaults to 'Basic')"
    )

    parser.add_argument(
        "-f", "--file-path",
        required=False,
        nargs="?",
        default=os.path.expanduser("~/.config/devops-overseer/credentials.yml"),
        help="File path to the credentials file (optional, defaults to ~/.config/devops-overseer/credentials.yml)"
    )

    def run(args):
        CredentialsManager.execute(args)

    parser.set_defaults(func=run)