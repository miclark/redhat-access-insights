"""
Handle adding files and preparing the archive for upload
"""
import tempfile
import time
import os
import shutil
import logging
from utilities import determine_hostname, _expand_paths
from constants import InsightsConstants as constants

logger = logging.getLogger(constants.app_name)


class InsightsArchive(object):

    """
    This class is an interface for adding command output
    and files to the insights archive
    """

    def __init__(self):
        """
        Initialize the Insights Archive
        Create temp dir, archive dir, and command dir
        """
        self.tmp_dir = tempfile.mkdtemp(prefix='/var/tmp/')
        self.archive_name = ("insights-%s-%s" %
                             (determine_hostname(),
                              time.strftime("%Y%m%d%H%M%S")))
        self.archive_dir = self.create_archive_dir()
        self.cmd_dir = self.create_command_dir()

    def create_archive_dir(self):
        """
        Create the archive dir
        """
        archive_dir = os.path.join(self.tmp_dir, self.archive_name)
        os.makedirs(archive_dir, 0o700)
        return archive_dir

    def create_command_dir(self):
        """
        Create the "sos_commands" dir
        """
        cmd_dir = os.path.join(self.archive_dir, "insights_commands")
        os.makedirs(cmd_dir, 0o700)
        return cmd_dir

    def get_full_archive_path(self, path):
        """
        Returns the full archive path
        """
        return os.path.join(self.archive_dir, path[1:])

    def _copy_file(self, path):
        """
        Copy just a single file
        """
        full_path = self.get_full_archive_path(path)
        # Try to make the dir, eat exception if it fails
        try:
            os.makedirs(os.path.dirname(full_path))
        except OSError:
            # This is really chatty :(
            # logger.debug("Could not create dir for %s" % os.path.dirname(full_path))
            pass
        logger.debug("Copying %s to %s", path, full_path)
        shutil.copyfile(path, full_path)
        return path

    def copy_file(self, path):
        """
        Copy a single file or regex, creating the necessary directories
        """
        if "*" in path:
            paths = _expand_paths(path)
            if paths:
                for path in paths:
                    self._copy_file(path)
        else:
            if os.path.isfile(path):
                return self._copy_file(path)
            else:
                logger.debug("File %s does not exist", path)
                return False

    def copy_dir(self, path):
        """
        Recursively copy directory
        """
        for directory in path:
            if os.path.isdir(path):
                full_path = os.path.join(self.archive_dir, directory[1:])
                logger.debug("Copying %s to %s", directory, full_path)
                shutil.copytree(directory, full_path)
            else:
                logger.debug("Not a directory: %s", directory)
        return path

    def create_tar_file(self):
        """
        Create tar file to be compressed
        """
        import tarfile
        tar_file_name = os.path.join(self.tmp_dir, self.archive_name)
        tar_file_name = tar_file_name + ".tar.gz"
        logger.debug("Tar File: " + tar_file_name)
        tar = tarfile.open(tar_file_name, "w|gz")
        tar.add(self.archive_dir, arcname=self.archive_name)
        tar.close()
        self.delete_archive_dir()
        logger.debug("Tar File Size: %s", str(os.path.getsize(tar_file_name)))
        return tar_file_name

    def delete_tmp_dir(self):
        """
        Delete the entire tmp dir
        """
        logger.debug("Deleting: " + self.tmp_dir)
        shutil.rmtree(self.tmp_dir, True)

    def delete_archive_dir(self):
        """
        Delete the entire archive dir
        """
        logger.debug("Deleting: " + self.archive_dir)
        shutil.rmtree(self.archive_dir, True)

    def add_command_output(self, command):
        """
        Add command output to file
        Use DataCollector.run_command_get_output to run the command
        """
        logger.debug("Writing %s to cmd_dir", command['cmd'])
        cmd_out = open(os.path.join(self.cmd_dir, command['cmd']), 'w')
        cmd_out.write(command['output'].encode('utf8'))
        cmd_out.close()
