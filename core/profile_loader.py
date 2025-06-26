"""Profile data loading and management."""

from typing import Optional, Tuple
from config.settings import settings
from utils.file_utils import read_linkedin_profile, read_summary_file, FileReadError
from utils.logger import logger
from core.models import UserProfile


class ProfileLoader:
    """Handles loading and caching of user profile data."""

    def __init__(self):
        """Initialize the profile loader."""
        self._cached_profile: Optional[UserProfile] = None
        self._profile_name = "Raphaël PICARD"  # Could be made configurable later
        logger.debug("ProfileLoader initialized")

    def get_name(self) -> str:
        """
        Get the user's name.

        Returns:
            The user's name
        """
        return self._profile_name

    def get_linkedin_content(self) -> str:
        """
        Load LinkedIn PDF content.

        Returns:
            LinkedIn profile content as string

        Raises:
            FileReadError: If LinkedIn file cannot be read
        """
        try:
            content = read_linkedin_profile(settings.PROFILE_DIR, settings.LINKEDIN_PDF)
            logger.debug(f"LinkedIn content loaded: {len(content)} characters")
            return content
        except FileReadError as e:
            logger.error(f"Failed to load LinkedIn content: {e}")
            raise

    def get_summary_content(self) -> str:
        """
        Load summary text content.

        Returns:
            Summary content as string

        Raises:
            FileReadError: If summary file cannot be read
        """
        try:
            content = read_summary_file(settings.PROFILE_DIR, settings.SUMMARY_TXT)
            logger.debug(f"Summary content loaded: {len(content)} characters")
            return content
        except FileReadError as e:
            logger.error(f"Failed to load summary content: {e}")
            raise

    def load_profile(self, use_cache: bool = True) -> UserProfile:
        """
        Load complete user profile data.

        Args:
            use_cache: Whether to use cached profile if available

        Returns:
            UserProfile object with all profile data

        Raises:
            FileReadError: If profile files cannot be read
        """
        if use_cache and self._cached_profile is not None:
            logger.debug("Using cached profile data")
            return self._cached_profile

        logger.info("Loading user profile data...")

        try:
            name = self.get_name()
            summary = self.get_summary_content()
            linkedin = self.get_linkedin_content()

            profile = UserProfile(name=name, summary=summary, linkedin_content=linkedin)

            # Cache the profile
            self._cached_profile = profile
            logger.info(f"Profile loaded successfully for {name}")

            return profile

        except FileReadError as e:
            logger.error(f"Failed to load profile: {e}")
            raise

    def get_profile_info(self, use_cache: bool = True) -> Tuple[str, str, str]:
        """
        Get profile information as tuple (for backward compatibility).

        Args:
            use_cache: Whether to use cached profile if available

        Returns:
            Tuple of (name, summary, linkedin_content)

        Raises:
            FileReadError: If profile files cannot be read
        """
        profile = self.load_profile(use_cache)
        return profile.profile_info

    def refresh_profile(self) -> UserProfile:
        """
        Force refresh the profile data from files.

        Returns:
            Refreshed UserProfile object

        Raises:
            FileReadError: If profile files cannot be read
        """
        logger.info("Refreshing profile data from files...")
        self._cached_profile = None
        return self.load_profile(use_cache=False)

    def is_profile_loaded(self) -> bool:
        """
        Check if profile is currently loaded in cache.

        Returns:
            True if profile is cached, False otherwise
        """
        return self._cached_profile is not None

    def clear_cache(self) -> None:
        """Clear the cached profile data."""
        logger.debug("Clearing profile cache")
        self._cached_profile = None


# Global profile loader instance
_profile_loader: Optional[ProfileLoader] = None


def get_profile_loader() -> ProfileLoader:
    """
    Get the global profile loader instance (singleton pattern).

    Returns:
        The configured ProfileLoader instance
    """
    global _profile_loader

    if _profile_loader is None:
        _profile_loader = ProfileLoader()

    return _profile_loader


# Convenience functions for backward compatibility
def get_name() -> str:
    """Get the user's name."""
    return get_profile_loader().get_name()


def get_linkedin() -> str:
    """Load LinkedIn profile content."""
    return get_profile_loader().get_linkedin_content()


def get_summary() -> str:
    """Load summary content."""
    return get_profile_loader().get_summary_content()


def get_info() -> Tuple[str, str, str]:
    """Get profile info as tuple (name, summary, linkedin)."""
    return get_profile_loader().get_profile_info()


def load_profile(use_cache: bool = True) -> UserProfile:
    """Load complete user profile."""
    return get_profile_loader().load_profile(use_cache)


def refresh_profile() -> UserProfile:
    """Force refresh profile data from files."""
    return get_profile_loader().refresh_profile()
