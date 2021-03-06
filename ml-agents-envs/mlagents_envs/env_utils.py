import glob
import os
import subprocess
from sys import platform
from typing import Optional, List
from mlagents_envs.logging_util import get_logger
from mlagents_envs.exception import UnityEnvironmentException


def validate_environment_path(env_path: str) -> Optional[str]:
    """
    Strip out executable extensions of the env_path
    :param env_path: The path to the executable
    """
    env_path = (
        env_path.strip()
        .replace(".app", "")
        .replace(".exe", "")
        .replace(".x86_64", "")
        .replace(".x86", "")
    )
    true_filename = os.path.basename(os.path.normpath(env_path))
    get_logger(__name__).debug("The true file name is {}".format(true_filename))

    if not (glob.glob(env_path) or glob.glob(env_path + ".*")):
        return None

    cwd = os.getcwd()
    launch_string = None
    true_filename = os.path.basename(os.path.normpath(env_path))
    if platform == "linux" or platform == "linux2":
        candidates = glob.glob(os.path.join(cwd, env_path) + ".x86_64")
        if len(candidates) == 0:
            candidates = glob.glob(os.path.join(cwd, env_path) + ".x86")
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".x86_64")
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".x86")
        if len(candidates) > 0:
            launch_string = candidates[0]

    elif platform == "darwin":
        candidates = glob.glob(
            os.path.join(cwd, env_path + ".app", "Contents", "MacOS", true_filename)
        )
        if len(candidates) == 0:
            candidates = glob.glob(
                os.path.join(env_path + ".app", "Contents", "MacOS", true_filename)
            )
        if len(candidates) == 0:
            candidates = glob.glob(
                os.path.join(cwd, env_path + ".app", "Contents", "MacOS", "*")
            )
        if len(candidates) == 0:
            candidates = glob.glob(
                os.path.join(env_path + ".app", "Contents", "MacOS", "*")
            )
        if len(candidates) > 0:
            launch_string = candidates[0]
    elif platform == "win32":
        candidates = glob.glob(os.path.join(cwd, env_path + ".exe"))
        if len(candidates) == 0:
            candidates = glob.glob(env_path + ".exe")
        if len(candidates) > 0:
            launch_string = candidates[0]
    return launch_string


def launch_executable(file_name: str, args: List[str]) -> subprocess.Popen:
    """
    Launches a Unity executable and returns the process handle for it.
    :param file_name: the name of the executable
    :param args: List of string that will be passed as command line arguments
    when launching the executable.
    """
    launch_string = validate_environment_path(file_name)
    if launch_string is None:
        raise UnityEnvironmentException(
            f"Couldn't launch the {file_name} environment. Provided filename does not match any environments."
        )
    else:
        get_logger(__name__).debug("This is the launch string {}".format(launch_string))
        # Launch Unity environment
        subprocess_args = [launch_string] + args
        try:
            return subprocess.Popen(
                subprocess_args,
                # start_new_session=True means that signals to the parent python process
                # (e.g. SIGINT from keyboard interrupt) will not be sent to the new process on POSIX platforms.
                # This is generally good since we want the environment to have a chance to shutdown,
                # but may be undesirable in come cases; if so, we'll add a command-line toggle.
                # Note that on Windows, the CTRL_C signal will still be sent.
                start_new_session=True,
            )
        except PermissionError as perm:
            # This is likely due to missing read or execute permissions on file.
            raise UnityEnvironmentException(
                f"Error when trying to launch environment - make sure "
                f"permissions are set correctly. For example "
                f'"chmod -R 755 {launch_string}"'
            ) from perm
